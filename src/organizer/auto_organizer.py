"""
DesktopAI
Auto Organizer Module (Enhanced with Windows File Lock Retries)
"""
import shutil
import time
import concurrent.futures
from pathlib import Path
from typing import List, Callable, Optional
from dataclasses import dataclass

from core.logger import get_logger
from scanner.scanner import FileScanner
from ai.categorizer import categorize_file
from organizer.action import OrganizationAction
from documents.pdf_reader import read_pdf_text
from documents.docx_reader import read_docx_text
from documents.excel_reader import read_excel_text
from documents.ocr_reader import read_image_text
from core import config

logger = get_logger("organizer")

@dataclass
class OrganizationPlan:
    actions: List[OrganizationAction]
    summary: dict

class AutoOrganizer:
    def __init__(self):
        self.scanner = FileScanner()
        self._history: List[OrganizationAction] = []
        self._is_cancelled = False

    def cancel(self): self._is_cancelled = True
    def reset_cancel(self): self._is_cancelled = False

    def analyze_and_plan(self, target_folder: Path, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> OrganizationPlan:
        self.reset_cancel()
        logger.info(f"Starting analysis of: {target_folder}")
        if progress_callback: progress_callback(0, 100, "Scanning folder structure...")
            
        files = self.scanner.scan(target_folder)
        total_files = len(files)
        if total_files == 0: return OrganizationPlan(actions=[], summary={"total": 0, "categorized": 0, "errors": 0})

        actions, categorized_count, error_count = [], 0, 0

        def process_file(file_item) -> Optional[OrganizationAction]:
            if self._is_cancelled: return None
            try:
                if isinstance(file_item, Path):
                    file_path, file_name, extension = file_item, file_item.name, file_item.suffix
                else:
                    file_path = getattr(file_item, 'path', Path(str(file_item)))
                    file_name = getattr(file_item, 'name', file_path.name)
                    extension = getattr(file_item, 'extension', file_path.suffix)
                
                content = self._extract_content(file_path, extension)
                parent_folder = file_path.parent.name if file_path.parent != target_folder else "Root"
                ai_result = categorize_file(file_name, extension, parent_folder, content or "")
                
                if ai_result:
                    category = ai_result["category"]
                    safe_category = "".join(c for c in category if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    dest_folder = target_folder / safe_category
                    dest_path = self._get_unique_path(dest_folder / file_name)
                    return OrganizationAction(source=file_path, destination=dest_path, status="pending", category=category, confidence=ai_result["confidence"], reason=ai_result["reason"])
                else:
                    dest_path = self._get_unique_path(target_folder / "Uncategorized" / file_name)
                    return OrganizationAction(source=file_path, destination=dest_path, status="pending", category="Uncategorized", confidence=0.0, reason="AI failed.")
            except Exception as e:
                logger.error(f"Error processing {file_name}: {e}")
                return None

        max_workers = getattr(config, 'MAX_WORKERS', 4)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(process_file, f): f for f in files}
            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                if self._is_cancelled:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                action = future.result()
                if action:
                    actions.append(action)
                    categorized_count += 1
                else: error_count += 1
                if progress_callback:
                    current_file = futures[future].name if hasattr(futures[future], 'name') else "Unknown"
                    progress_callback(int((i + 1) / total_files * 100), 100, f"Analyzing: {current_file}")

        return OrganizationPlan(actions=actions, summary={"total": total_files, "categorized": categorized_count, "errors": error_count, "cancelled": self._is_cancelled})

    def _extract_content(self, file_path: Path, extension: str) -> Optional[str]:
        ext = extension.lower()
        try:
            if ext in ['.pdf']: return read_pdf_text(file_path)
            elif ext in ['.docx']: return read_docx_text(file_path)
            elif ext in ['.xlsx', '.xls']: return read_excel_text(file_path)
            elif ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.heic']: return read_image_text(file_path)
            elif ext in ['.txt', '.md', '.csv', '.json', '.py', '.js', '.html', '.css']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f: return f.read(2000)
            return None
        except Exception as e:
            return None

    def _get_unique_path(self, target_path: Path) -> Path:
        if not target_path.exists(): return target_path
        stem, suffix = target_path.stem, target_path.suffix
        counter = 1
        while True:
            new_path = target_path.parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists(): return new_path
            counter += 1

    def apply_plan(self, plan: OrganizationPlan, progress_callback: Optional[Callable[[int, int, str], None]] = None) -> List[OrganizationAction]:
        actions = plan.actions
        total = len(actions)
        
        for i, action in enumerate(actions):
            if self._is_cancelled: break
            try:
                if not action.source.exists():
                    action.status, action.reason = "failed", "Source missing"
                    continue
                if action.destination.exists():
                    action.status, action.reason = "skipped", "Dest exists"
                    continue
                    
                # Windows Long Path Check
                if len(str(action.destination)) > 250:
                    action.status, action.reason = "failed", "Path too long for Windows"
                    continue

                action.destination.parent.mkdir(parents=True, exist_ok=True)
                
                # Retry mechanism for Windows File Locks (Antivirus/Word)
                moved = False
                for attempt in range(3):
                    try:
                        shutil.move(str(action.source), str(action.destination))
                        moved = True
                        break
                    except PermissionError:
                        if attempt < 2: time.sleep(1.5) # Wait and retry
                        else: raise
                
                if moved:
                    action.status = "moved"
                    self._history.append(action)
                    
            except PermissionError:
                action.status, action.reason = "failed", "Permission denied (File locked?)"
            except Exception as e:
                action.status, action.reason = "failed", str(e)
                
            if progress_callback:
                progress_callback(int((i + 1) / total * 100), 100, f"Moving: {action.source.name}")
        return actions

    def undo_last(self) -> List[OrganizationAction]:
        undone_actions = []
        while self._history:
            action = self._history.pop()
            if action.status == "moved":
                try:
                    if action.destination.exists():
                        action.source.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(action.destination), str(action.source))
                        action.status = "undone"
                        undone_actions.append(action)
                except Exception as e:
                    action.status = "failed_undo"
        return undone_actions