"""
DesktopAI v2.0 — History store guard test
File: tests/unit/test_history_store.py
"""
from __future__ import annotations
import uuid

from infrastructure.storage.database import DB


def test_history_roundtrip_and_undo():
    DB.connect()
    batch = f"unit-{uuid.uuid4().hex[:8]}"

    hid = DB.record_history_entry(
        action_type="move",
        source_path="D:/a/x.pdf",
        target_path="D:/b/PDFs/x.pdf",
        category="PDFs",
        confidence=0.95,
        model="test",
        status="completed",
        batch_id=batch,
    )
    assert hid

    rows = DB.get_history(batch_id=batch)
    assert len(rows) == 1
    assert rows[0]["action_type"] == "move"

    DB.mark_history_undone(hid)
    assert len(DB.get_history(batch_id=batch, status="undone")) == 1
    assert len(DB.get_history(batch_id=batch, status="completed")) == 0