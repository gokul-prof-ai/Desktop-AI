"""
DesktopAI
AI Planner (Phase 12)

Turns a plain-English goal into an ordered sequence of steps,
executes them, and explains what was done and why. This is the
highest-level module in DesktopAI — it orchestrates Scanner,
Database, Documents, AI, Memory, and Organizer together.

The Planner never moves files on its own. It produces an
OrganizationAction list that still requires Organizer.preview()
and Organizer.apply() — the user always sees and approves moves
before anything changes on disk.
"""

from dataclasses import dataclass, field
from pathlib import Path

from ai.classifier import classify_file
from ai.ollama_client import generate_response
from ai.recommender import recommend_action
from core import config
from core.logger import get_logger
from database.database import DatabaseManager
from memory.memory_store import MemoryStore
from organizer.action import OrganizationAction
from scanner.file_info import FileInfo
from scanner.scanner import FileScanner
from watcher.suggestion_engine import extract_text

logger = get_logger("planner")


@dataclass
class PlanStep:
    """One step in an execution plan."""
    name: str
    description: str
    status: str = "pending"   # pending, completed, failed, skipped
    result: str = ""


@dataclass
class Plan:
    """A complete plan: its goal, ordered steps, and final summary."""
    goal: str
    folder: Path
    steps: list[PlanStep] = field(default_factory=list)
    actions: list[OrganizationAction] = field(default_factory=list)
    summary: str = ""


class AIPlan:
    """
    Orchestrates a multi-step file organisation plan for a folder.

    Usage:
        planner = AIPlan()
        plan    = planner.create_plan(folder, goal="Organise my Downloads")
        planner.execute(plan)
        print(plan.summary)
        # Then show plan.actions via Organizer.preview() before applying.
    """

    def create_plan(self, folder: Path, goal: str = "Organise files") -> Plan:
        """
        Build a Plan object describing what will be done for this
        folder. Does not execute anything yet.
        """
        plan = Plan(goal=goal, folder=folder)
        plan.steps = [
            PlanStep("scan",      f"Scan '{folder.name}' and collect file metadata."),
            PlanStep("classify",  "Use AI to classify each file by content type."),
            PlanStep("recommend", "Use memory + AI to recommend a destination folder."),
            PlanStep("save",      "Save scan results to the DesktopAI database."),
            PlanStep("explain",   "Generate a human-readable summary of the plan."),
        ]
        logger.info("Created plan for goal: %s", goal)
        return plan

    def execute(self, plan: Plan) -> Plan:
        """
        Run each step in the plan in order. Updates each step's
        status and result in place. Populates plan.actions with
        OrganizationAction objects ready for Organizer.preview().
        """
        files: list[FileInfo] = []

        for step in plan.steps:
            try:
                if step.name == "scan":
                    files = self._step_scan(plan.folder)
                    step.result = f"Found {len(files)} file(s)."

                elif step.name == "classify":
                    if not files:
                        step.status = "skipped"
                        step.result = "No files to classify."
                        continue
                    self._step_classify(files)
                    classified = sum(1 for f in files if getattr(f, "_category", None))
                    step.result = f"Classified {classified}/{len(files)} file(s)."

                elif step.name == "recommend":
                    if not files:
                        step.status = "skipped"
                        step.result = "No files to recommend for."
                        continue
                    plan.actions = self._step_recommend(files, plan.folder)
                    step.result = f"Created {len(plan.actions)} organisation action(s)."

                elif step.name == "save":
                    self._step_save(files)
                    step.result = f"Saved {len(files)} record(s) to database."

                elif step.name == "explain":
                    plan.summary = self._step_explain(plan)
                    step.result = "Summary generated."

                step.status = "completed"

            except Exception as error:
                step.status = "failed"
                step.result = f"Error: {error}"
                logger.warning("Step '%s' failed: %s", step.name, error)

        logger.info(
            "Plan executed: %d/%d steps completed.",
            sum(1 for s in plan.steps if s.status == "completed"),
            len(plan.steps),
        )
        return plan

    def _step_scan(self, folder: Path) -> list[FileInfo]:
        scanner = FileScanner()
        return scanner.scan(folder)

    def _step_classify(self, files: list[FileInfo]) -> None:
        memory = MemoryStore(config.MEMORY_PATH)
        memory.connect()
        for file_info in files:
            text = extract_text(file_info.path)
            category = classify_file(text) if text else None
            file_info._category = category  # type: ignore[attr-defined]
            preferred = memory.get_preferred_folder(category) if category else None
            file_info._preferred_folder = preferred  # type: ignore[attr-defined]
        memory.close()

    def _step_recommend(
        self, files: list[FileInfo], base_folder: Path
    ) -> list[OrganizationAction]:
        actions: list[OrganizationAction] = []
        for file_info in files:
            category = getattr(file_info, "_category", None)
            preferred = getattr(file_info, "_preferred_folder", None)

            if preferred:
                destination_folder = preferred
            else:
                text = extract_text(file_info.path)
                destination_folder = recommend_action(
                    file_info.name, category=category, text=text
                )

            if not destination_folder:
                continue

            actions.append(OrganizationAction(
                source=file_info.path,
                destination=base_folder / destination_folder / file_info.name,
            ))
        return actions

    def _step_save(self, files: list[FileInfo]) -> None:
        db = DatabaseManager(config.DATABASE_PATH)
        db.connect()
        for file_info in files:
            db.save_file(file_info)
        db.close()

    def _step_explain(self, plan: Plan) -> str:
        step_lines = "\n".join(
            f"- {s.name}: {s.result} [{s.status}]"
            for s in plan.steps if s.name != "explain"
        )
        prompt = (
            f"You are DesktopAI. A user asked you to: '{plan.goal}'.\n\n"
            f"You scanned '{plan.folder.name}' and completed these steps:\n"
            f"{step_lines}\n\n"
            f"You prepared {len(plan.actions)} file move(s) for the user to review.\n\n"
            f"Write a short, friendly 2-3 sentence explanation of what you found "
            f"and what you're suggesting. Do not use bullet points."
        )
        explanation = generate_response(prompt)

        if explanation is None:
            completed = sum(1 for s in plan.steps if s.status == "completed")
            explanation = (
                f"Scanned '{plan.folder.name}' and completed "
                f"{completed} of {len(plan.steps)} steps. "
                f"Prepared {len(plan.actions)} file move(s) for your review."
            )
        return explanation