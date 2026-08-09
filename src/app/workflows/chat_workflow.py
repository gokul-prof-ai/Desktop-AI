"""
DesktopAI v2.0 — Chat Workflow
File: src/app/workflows/chat_workflow.py

The AI agent brain. Answers greetings and file questions from REAL
database data (no AI call needed), and routes open-ended questions
to the AI Gateway with rich context so it answers like an agent,
not a raw classifier.
"""
from __future__ import annotations

from core.logger import get_logger
from infrastructure.ai.gateway import AIGateway, GenerateRequest
from infrastructure.storage.database import DB

logger = get_logger(__name__)

_GREETINGS = {"hi", "hello", "hey", "yo", "hii", "good morning", "good evening", "what's up", "whats up"}

_SYSTEM = (
    "You are DesktopAI, a friendly local file-organization agent. "
    "Answer in 2-4 concise sentences using the CONTEXT provided. "
    "Never mention being a mock or a model."
)


class ChatWorkflow:
    def ask(self, message: str) -> str:
        low = message.strip().lower()
        stats = DB.get_stats()

        # 1) Greetings — instant, data-aware
        if low in _GREETINGS:
            return (
                f"Hello! I'm DesktopAI — your local file agent. I'm currently tracking "
                f"{stats['total_files']} files and {stats['total_operations']} completed operations. "
                f"Ask me 'what are these files?' or tell me what you'd like to organize."
            )

        # 2) Questions about files — answered from the database
        if "file" in low:
            cats = stats["categories"]
            if cats:
                top = sorted(cats.items(), key=lambda kv: kv[1], reverse=True)[:5]
                breakdown = ", ".join(f"{name} ({n})" for name, n in top)
                return (
                    f"You have {stats['total_files']} tracked files. Breakdown: {breakdown}. "
                    f"Run a new scan from Home any time to refresh this."
                )
            return (
                "I haven't scanned anything yet. Open Home, drop a folder, "
                "and I'll tell you exactly what's in it."
            )

        # 3) Organization requests — guided answer
        if any(k in low for k in ("organize", "tidy", "clean", "sort")):
            return (
                "Happy to! Scan a folder in Home, switch to Organize, review the plan, "
                "and hit Apply. I'll move everything into category folders — and you can "
                "Undo the whole batch if you change your mind."
            )

        # 4) Thanks
        if "thank" in low:
            return "You're welcome! Anything else — finding, organizing, or explaining files?"

        # 5) Open-ended — AI with real context
        cats = ", ".join(f"{k}: {v}" for k, v in list(stats["categories"].items())[:6]) or "none yet"
        context = (
            f"CONTEXT: tracked_files={stats['total_files']}; "
            f"completed_operations={stats['total_operations']}; categories={cats}."
        )
        try:
            resp = AIGateway.generate(GenerateRequest(
                prompt=f"{context}\nThe user says: {message}\nRespond as DesktopAI (2-4 sentences).",
                system=_SYSTEM,
                temperature=0.4,
                max_tokens=150,
            ))
            return resp.text
        except Exception as exc:
            logger.warning("Chat AI call failed: %s", exc)
            return (
                "I can't reach the AI backend right now, but I'm still fully functional "
                "for scanning, organizing, and reporting on your files from the other tabs."
            )