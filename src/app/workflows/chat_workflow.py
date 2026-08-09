"""
DesktopAI v2.0 — Chat Workflow (AI agent)
File: src/app/workflows/chat_workflow.py

Uses Ollama when healthy, MockProvider in --mock-ai mode, and always
falls back to data-aware local answers so the bot never dies.
"""
from __future__ import annotations

from core.logger import get_logger
from infrastructure.ai.gateway import AIGateway, GenerateRequest
from infrastructure.storage.database import DB

logger = get_logger(__name__)

_GREETINGS = {"hi", "hello", "hey", "yo", "hii", "good morning", "good evening", "whats up", "what's up"}

_SYSTEM = (
    "You are DesktopAI, a friendly local file-organization agent running on the user's machine. "
    "Answer in 2-4 concise sentences using the CONTEXT provided. Never mention being a mock."
)


class ChatWorkflow:
    def ask(self, message: str) -> str:
        low = message.strip().lower()
        stats = self._safe_stats()

        if low in _GREETINGS:
            return (
                f"Hello! I'm DesktopAI — your local file agent. I'm tracking "
                f"{stats['total_files']} files and {stats['total_operations']} completed operations. "
                f"Ask 'what are these files?' or tell me what to organize."
            )

        if "thank" in low:
            return "You're welcome! Anything else — finding, organizing, or explaining files?"

        if any(k in low for k in ("organize", "tidy", "clean", "sort")):
            return (
                "Scan a folder in Home, switch to Organize, review the plan, and hit Apply. "
                "I'll move everything into category folders — and Undo restores the whole batch."
            )

        if "file" in low:
            cats = stats["categories"]
            if cats:
                top = sorted(cats.items(), key=lambda kv: kv[1], reverse=True)[:5]
                breakdown = ", ".join(f"{name} ({n})" for name, n in top)
                return f"You have {stats['total_files']} tracked files. Breakdown: {breakdown}."
            return "I haven't scanned anything yet. Drop a folder in Home and I'll analyze it."

        # Open-ended → AI (Ollama or Mock) with real context
        return self._ask_ai(message, stats)

    def _ask_ai(self, message: str, stats: dict) -> str:
        cats = ", ".join(f"{k}: {v}" for k, v in list(stats["categories"].items())[:6]) or "none yet"
        context = (
            f"CONTEXT: tracked_files={stats['total_files']}; "
            f"completed_operations={stats['total_operations']}; categories={cats}."
        )
        try:
            if not AIGateway.health_check():
                return (
                    "The AI backend isn't reachable. Start Ollama (`ollama serve`) or run with "
                    "--mock-ai. Scanning and organizing still work from the other tabs."
                )
            resp = AIGateway.generate(GenerateRequest(
                prompt=f"{context}\nThe user says: {message}\nRespond as DesktopAI (2-4 sentences).",
                system=_SYSTEM,
                temperature=0.4,
                max_tokens=160,
            ))
            return resp.text.strip() or "I don't have an answer for that yet."
        except Exception as exc:
            logger.warning("Chat AI failed: %s", exc)
            return (
                "I hit a problem reaching the AI backend, but I can still scan, organize, "
                "and report on your files from the other tabs."
            )

    @staticmethod
    def _safe_stats() -> dict:
        try:
            return DB.get_stats()
        except Exception:
            return {"total_files": 0, "total_operations": 0, "categories": {}}