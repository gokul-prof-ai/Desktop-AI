"""
DesktopAI
Tests for the Memory Store module.
"""

import pytest

from core.exceptions import DatabaseNotConnectedError
from memory.memory_store import MemoryStore


def test_connect_creates_database_file(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    store.connect()
    assert (tmp_path / "memory.db").exists()
    store.close()


def test_operations_before_connect_raise_clear_error(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    with pytest.raises(DatabaseNotConnectedError):
        store.get_preferred_folder("Invoice")


def test_record_and_retrieve_folder_preference(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    store.connect()
    store.record_folder_choice("Invoice", "Documents/Invoices")
    assert store.get_preferred_folder("Invoice") == "Documents/Invoices"
    store.close()


def test_most_used_folder_is_preferred(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    store.connect()
    store.record_folder_choice("Invoice", "Documents/Invoices")
    store.record_folder_choice("Invoice", "Documents/Invoices")
    store.record_folder_choice("Invoice", "Work/Bills")
    assert store.get_preferred_folder("Invoice") == "Documents/Invoices"
    store.close()


def test_get_preferred_folder_returns_none_for_unknown_category(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    store.connect()
    assert store.get_preferred_folder("Unknown") is None
    store.close()


def test_get_all_preferences_returns_sorted_results(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    store.connect()
    store.record_folder_choice("Invoice", "Documents/Invoices")
    store.record_folder_choice("Invoice", "Documents/Invoices")
    store.record_folder_choice("Resume", "Documents/Resumes")
    prefs = store.get_all_preferences()
    assert len(prefs) == 2
    assert prefs[0]["folder"] == "Documents/Invoices"
    assert prefs[0]["use_count"] == 2
    store.close()


def test_record_and_retrieve_feedback(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    store.connect()
    store.record_feedback("a.pdf", True, "Invoice", "Documents/Invoices")
    store.record_feedback("b.pdf", True, "Invoice", "Documents/Invoices")
    store.record_feedback("c.pdf", False, "Invoice", "Work/Bills")
    assert store.get_acceptance_rate("Invoice") == round(2 / 3, 2)
    store.close()


def test_acceptance_rate_returns_none_for_unknown_category(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")
    store.connect()
    assert store.get_acceptance_rate("Unknown") is None
    store.close()


def test_preferences_persist_across_reconnect(tmp_path):
    """Data saved in one session should still be there after
    closing and reconnecting."""
    db_path = tmp_path / "memory.db"
    store = MemoryStore(db_path)
    store.connect()
    store.record_folder_choice("Invoice", "Documents/Invoices")
    store.close()

    store2 = MemoryStore(db_path)
    store2.connect()
    assert store2.get_preferred_folder("Invoice") == "Documents/Invoices"
    store2.close()