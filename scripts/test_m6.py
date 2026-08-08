"""
DesktopAI v2.0 — Milestone 6 Verification Script

File:
    scripts/test_m6.py

Purpose:
    Verifies the core functionality introduced/required for
    Milestone 6:

    1. FileInfo dataclass
    2. Fast-rule classification
    3. AI fallback classification
    4. File scanning
    5. Batch classification

Design goals:
    - Deterministic
    - Self-contained
    - Safe to run repeatedly
    - Does not modify production data
    - Does not depend on a specific unknown extension
    - Produces clear diagnostics when something fails
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path


# ================================================================
# PROJECT PATH SETUP
# ================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


# ================================================================
# TEST CONFIGURATION
# ================================================================

TEST_DOCUMENT_PATH = Path("D:/docs/report.pdf")
TEST_AI_PATH = Path("D:/docs/milestone6_unknown_file.zzz")

TEST_PDF_EXTENSION = ".pdf"

# Extensions that are commonly used by the application.
# These are intentionally avoided when searching for an unknown
# extension for the AI fallback test.
COMMON_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".csv",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".zip",
    ".rar",
    ".7z",
    ".mp3",
    ".wav",
    ".mp4",
    ".avi",
    ".mkv",
    ".py",
    ".js",
    ".ts",
    ".json",
    ".xml",
    ".html",
    ".css",
}


# ================================================================
# HELPER FUNCTIONS
# ================================================================


def print_header(title: str) -> None:
    """Print a consistent test section header."""
    print(title)


def print_success(message: str) -> None:
    """Print a successful test message."""
    print(f"  ✓ {message}")


def print_failure(message: str) -> None:
    """Print a failure message."""
    print(f"  ✗ {message}")


def find_unknown_extension(classifier) -> str:
    """
    Find an extension that does not trigger the classifier's
    fast-rule stage.

    This is intentionally dynamic.

    The previous verification used '.xyz', but '.xyz' turned out
    to be recognized by the project's fast-rule system as 'Data'.

    Instead of hard-coding one extension, this function tests a
    sequence of deliberately unusual extensions and returns the
    first one that reaches the AI stage.

    Returns:
        str:
            An extension that should reach the AI classifier.

    Raises:
        RuntimeError:
            If every candidate is classified by the fast-rule stage.
    """

    candidates = [
        ".zzz",
        ".qzx",
        ".xqv",
        ".m6x",
        ".dai",
        ".unknown",
        ".desktopai",
        ".mystery",
    ]

    from domain.scanner.file_info import FileInfo

    for extension in candidates:
        if extension in COMMON_EXTENSIONS:
            continue

        test_file = FileInfo(
            path=Path(f"D:/docs/milestone6_probe{extension}"),
            filename=f"milestone6_probe{extension}",
            extension=extension,
            size_bytes=1024,
        )

        try:
            result = classifier.classify(test_file)
        except Exception as exc:
            raise RuntimeError(
                f"Classifier failed while probing extension "
                f"{extension}: {exc}"
            ) from exc

        if result.method == "ai":
            return extension

    raise RuntimeError(
        "Could not find an extension that reaches the AI stage. "
        "All candidate extensions were handled by fast rules. "
        "Review the classifier's fast-rule configuration."
    )


def close_database_safely(db) -> None:
    """Close the database without hiding the original test failure."""
    try:
        db.close()
    except Exception as exc:
        print(f"  Warning: database cleanup failed: {exc}")


# ================================================================
# MAIN VERIFICATION
# ================================================================


def main() -> None:
    """Run the complete Milestone 6 verification."""

    print()
    print("=" * 60)
    print("  DesktopAI v2.0 — Milestone 6 Verification")
    print("=" * 60)
    print()

    db = None

    try:
        # --------------------------------------------------------
        # SYSTEM INITIALIZATION
        # --------------------------------------------------------

        from core.logger import configure

        configure(debug=False)

        from infrastructure.config.settings import Settings

        Settings.load()

        # --------------------------------------------------------
        # MOCK AI PROVIDER
        # --------------------------------------------------------

        from infrastructure.ai.gateway import AIGateway
        from infrastructure.ai.mock_provider import MockProvider

        mock = MockProvider(
            default_response="Documents",
            delay_ms=0,
        )

        # Explicit responses used by the verification.
        mock.set_response("invoice", "Finance")
        mock.set_response(".pdf", "PDFs")
        mock.set_response(".jpg", "Images")

        AIGateway.set_provider(mock)

        # --------------------------------------------------------
        # DATABASE
        # --------------------------------------------------------

        from infrastructure.storage.database import DB

        db = DB
        db.connect()

        # ========================================================
        # TEST 1 — FILEINFO
        # ========================================================

        print_header("Test 1: FileInfo dataclass")

        from domain.scanner.file_info import FileInfo

        file_info = FileInfo(
            path=Path("D:/docs/invoice_jan_2026.pdf"),
            filename="invoice_jan_2026.pdf",
            extension=".pdf",
            size_bytes=204_800,
            modified_at=datetime.now(timezone.utc),
        )

        print(f"  Created    : {file_info}")
        print(f"  Size       : {file_info.display_size}")
        print(f"  Has text   : {file_info.has_text}")
        print(f"  Classified : {file_info.is_classified}")

        enriched = file_info.with_category(
            "Finance",
            0.94,
        )

        print(f"  Enriched   : {enriched}")
        print(f"  Confidence : {enriched.confidence_pct}")

        assert enriched.category == "Finance", (
            f"Expected Finance, got {enriched.category}"
        )

        assert enriched.confidence == 0.94, (
            f"Expected confidence 0.94, "
            f"got {enriched.confidence}"
        )

        print_success("FileInfo OK")
        print()

        # ========================================================
        # TEST 2 — FAST RULE CLASSIFICATION
        # ========================================================

        print_header(
            "Test 2: Classifier — fast rule (extension match)"
        )

        from domain.classifier.classifier import FileClassifier

        classifier = FileClassifier()

        pdf_file = FileInfo(
            path=TEST_DOCUMENT_PATH,
            filename="report.pdf",
            extension=TEST_PDF_EXTENSION,
            size_bytes=102_400,
        )

        result = classifier.classify(pdf_file)

        print(f"  File       : {pdf_file.filename}")
        print(f"  Category   : {result.category}")
        print(f"  Method     : {result.method}")
        print(
            f"  Confidence : "
            f"{int(result.confidence * 100)}%"
        )

        assert result.method == "fast_rule", (
            "Fast-rule classification failed: "
            f"expected 'fast_rule', got '{result.method}'"
        )

        assert result.category == "PDFs", (
            "Fast-rule classification failed: "
            f"expected 'PDFs', got '{result.category}'"
        )

        assert result.confidence > 0, (
            "Fast-rule classification returned zero confidence"
        )

        print_success("Fast rule classification OK")
        print()

        # ========================================================
        # TEST 3 — AI FALLBACK
        # ========================================================

        print_header(
            "Test 3: Classifier — AI stage (unknown extension)"
        )

        # Dynamically locate an extension that actually reaches
        # the AI stage.
        unknown_extension = find_unknown_extension(
            classifier
        )

        unknown_file = FileInfo(
            path=Path(
                f"D:/docs/"
                f"milestone6_unknown_file"
                f"{unknown_extension}"
            ),
            filename=(
                f"milestone6_unknown_file"
                f"{unknown_extension}"
            ),
            extension=unknown_extension,
            size_bytes=1024,
        )

        ai_calls_before = mock.call_count

        result = classifier.classify(unknown_file)

        ai_calls_after = mock.call_count

        print(
            f"  File       : "
            f"{unknown_file.filename}"
        )
        print(f"  Category   : {result.category}")
        print(f"  Method     : {result.method}")
        print(f"  AI calls   : {mock.call_count}")
        print(f"  Extension  : {unknown_extension}")

        assert result.method == "ai", (
            "AI fallback classification failed: "
            f"expected 'ai', got '{result.method}'"
        )

        assert result.category == "Documents", (
            "AI fallback returned unexpected category: "
            f"expected 'Documents', got "
            f"'{result.category}'"
        )

        assert ai_calls_after > ai_calls_before, (
            "AI provider was not called during AI fallback"
        )

        print_success("AI fallback classification OK")
        print()

        # ========================================================
        # TEST 4 — FILE SCANNER
        # ========================================================

        print_header(
            "Test 4: FileScanner on project data/ folder"
        )

        from domain.scanner.scanner import FileScanner

        data_directory = PROJECT_ROOT / "data"

        scanner = FileScanner()

        try:
            scanned_files = scanner.scan(data_directory)

            print(
                f"  Folder     : "
                f"{data_directory}"
            )
            print(
                f"  Files      : "
                f"{len(scanned_files)} found"
            )

            for scanned_file in scanned_files:
                print(
                    f"    → "
                    f"{scanned_file.filename} "
                    f"({scanned_file.display_size})"
                )

            print_success("Scanner OK")

        except Exception as exc:
            raise RuntimeError(
                f"FileScanner failed: {exc}"
            ) from exc

        print()

        # ========================================================
        # TEST 5 — BATCH CLASSIFICATION
        # ========================================================

        print_header("Test 5: Batch classification")

        test_files = [
            FileInfo(
                path=Path(
                    f"D:/docs/file{i}.pdf"
                ),
                filename=f"file{i}.pdf",
                extension=".pdf",
                size_bytes=1024,
            )
            for i in range(5)
        ]

        results = classifier.classify_batch(
            test_files
        )

        print(
            f"  Input files : "
            f"{len(test_files)}"
        )
        print(
            f"  Results     : "
            f"{len(results)}"
        )

        assert len(results) == len(test_files), (
            "Batch classification returned an incorrect "
            f"number of results: expected "
            f"{len(test_files)}, got {len(results)}"
        )

        for result in results:
            print(
                f"    → "
                f"{result.file_info.filename}: "
                f"{result.category} "
                f"[{result.method}]"
            )

            assert result.category == "PDFs", (
                "Unexpected batch category for "
                f"{result.file_info.filename}: "
                f"{result.category}"
            )

            assert result.method == "fast_rule", (
                "Unexpected batch classification method for "
                f"{result.file_info.filename}: "
                f"{result.method}"
            )

        print_success("Batch classification OK")
        print()

        # ========================================================
        # FINAL RESULT
        # ========================================================

        print("=" * 60)
        print("  Milestone 6 — All tests passed ✓")
        print("=" * 60)
        print()

    except AssertionError as exc:
        print()
        print("=" * 60)
        print("  Milestone 6 — VERIFICATION FAILED")
        print("=" * 60)
        print()
        print(f"  Assertion: {exc}")
        print()
        raise

    except Exception as exc:
        print()
        print("=" * 60)
        print("  Milestone 6 — VERIFICATION ERROR")
        print("=" * 60)
        print()
        print(f"  Error: {exc}")
        print()
        raise

    finally:
        if db is not None:
            close_database_safely(db)


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main()