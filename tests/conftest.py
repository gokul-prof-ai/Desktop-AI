"""
DesktopAI v2.0 — Test Configuration
File: tests/conftest.py

- Adds src/ to sys.path so tests can import core/, domain/, infrastructure/.
- Excludes v1_legacy/ (V1 tests preserved for reference, not part of V2 runs).
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# Never collect the preserved V1 legacy tests.
collect_ignore = ["v1_legacy"]