"""
DesktopAI v2.0 — Organization Planner
File: src/domain/organizer/planner.py

Analyzes files and generates a conflict-free organization plan.
"""
from __future__ import annotations
from pathlib import Path
from typing import Optional

from core.logger import get_logger
from domain.scanner.file_info import AnalysisResult, FileInfo
from domain.classifier.classifier import FileClassifier
from domain.organizer.action import OrganizationAction
from infrastructure.storage.memory_store import MemoryStore

logger = get_logger(__name__)


class OrganizationPlanner:
    """
    Generates a safe, conflict-checked organization plan.
    """
    
    def __init__(self) -> None:
        self._classifier = FileClassifier()
    
    def create_plan(
        self,
        files: list[FileInfo],
        target_base_folder: Path,
    ) -> list[OrganizationAction]:
        """
        Analyze files and generate a list of OrganizationActions.
        """
        logger.info(
            "Planner: creating plan for %d files → %s",
            len(files),
            target_base_folder,
        )
        
        results = self._classifier.classify_batch(files)
        planned_targets: set[Path] = set()
        actions: list[OrganizationAction] = []
        skipped_count = 0
        
        for result in results:
            if result.skipped:
                skipped_count += 1
                logger.debug(
                    "Planner: skipping %s — %s",
                    result.file_info.filename,
                    result.skip_reason,
                )
                continue
            
            action = self._build_action(result, target_base_folder, planned_targets)
            if action:
                actions.append(action)
                planned_targets.add(action.planned_target_path)
        
        logger.info(
            "Planner: generated %d actions (%d skipped, %d total files)",
            len(actions),
            skipped_count,
            len(files),
        )
        
        return actions
    
    def _build_action(
        self,
        result: AnalysisResult,
        target_base_folder: Path,
        planned_targets: set[Path],
    ) -> Optional[OrganizationAction]:
        """
        Build an OrganizationAction for a classified file.
        """
        file_info = result.file_info
        category = result.category
        
        target_folder = self._determine_target_folder(
            file_info, category, target_base_folder
        )
        
        target_path = self._get_unique_path(
            file_info.path,
            target_folder,
            planned_targets,
        )
        
        if self._is_already_in_place(file_info.path, target_path):
            logger.debug(
                "Planner: %s already in correct location",
                file_info.filename,
            )
            return None
        
        return OrganizationAction(
            action_type="move",
            source_path=file_info.path,
            planned_target_path=target_path,
            category=category,
            confidence=result.confidence,
        )
    
    def _determine_target_folder(
        self,
        file_info: FileInfo,
        category: str,
        target_base_folder: Path,
    ) -> Path:
        """
        Determine where this file should go.
        """
        preferred = MemoryStore.get_preferred_folder(
            file_info.filename,
            file_info.extension,
        )
        
        if preferred:
            target_folder = Path(preferred)
            logger.debug(
                "Planner: memory override — %s → %s",
                file_info.filename,
                target_folder,
            )
        else:
            target_folder = target_base_folder / category
        
        target_folder.mkdir(parents=True, exist_ok=True)
        
        return target_folder
    
    def _get_unique_path(
        self,
        source_path: Path,
        target_folder: Path,
        planned_targets: set[Path],
    ) -> Path:
        """
        Generate a unique target path, resolving naming conflicts.
        """
        stem = source_path.stem
        suffix = source_path.suffix
        target_path = target_folder / source_path.name
        
        # Debug: Check if the target already exists
        if target_path.exists():
            logger.info(
                "Planner: CONFLICT DETECTED — %s already exists at %s",
                source_path.name,
                target_path,
            )
        
        counter = 1
        while target_path.exists() or target_path in planned_targets:
            new_name = f"{stem}_{counter}{suffix}"
            target_path = target_folder / new_name
            counter += 1
            logger.debug(
                "Planner: conflict resolved — trying %s",
                target_path.name,
            )
        
        return target_path
    
    def _is_already_in_place(self, source_path: Path, target_path: Path) -> bool:
        """
        Check if the file is already in the correct location.
        """
        try:
            return source_path.resolve() == target_path.resolve()
        except Exception:
            return str(source_path) == str(target_path)