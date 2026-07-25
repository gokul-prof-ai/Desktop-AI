"""
DesktopAI
Integration Tests

Unlike the other test files (which test one module in isolation),
these tests chain multiple real modules together, the way the app
actually uses them — proving the pieces work correctly as a whole
pipeline, not just individually.

AI calls (classification, embeddings) are mocked rather than using
a real Ollama connection, so these tests run reliably on any
machine regardless of whether Ollama is installed there.
"""

import fitz
import ai.classifier as classifier_module
import ai.recommender as recommender_module
import search.embedder as embedder_module
from database.database import DatabaseManager
from documents.pdf_reader import read_pdf_text
from organizer.action import OrganizationAction
from organizer.organizer import Organizer
from scanner.scanner import FileScanner
from search.index_manager import SearchIndex
from watcher.suggestion_engine import build_suggestion, extract_text


# ---------------------------------------------------------------------------
# Pipeline 1: Scan → save to DB → reload
# ---------------------------------------------------------------------------

def test_scan_store_and_reload_pipeline(tmp_path):
    """Full pipeline: scan real files on disk -> save each to a real
    SQLite database -> load them back -> confirm the reloaded data
    matches what the scanner actually found."""

    (tmp_path / "notes.txt").write_text("Meeting notes for Q3 planning.")
    (tmp_path / "budget.txt").write_text("Q3 budget: $50,000 allocated.")

    scanner = FileScanner()
    scanned_files = scanner.scan(tmp_path)
    assert len(scanned_files) == 2

    db = DatabaseManager(tmp_path / "test_pipeline.db")
    db.connect()
    for file_info in scanned_files:
        db.save_file(file_info)

    reloaded_files = db.load_files()
    db.close()

    assert len(reloaded_files) == 2

    reloaded_names = {f.name for f in reloaded_files}
    scanned_names = {f.name for f in scanned_files}
    assert reloaded_names == scanned_names

    # Hashes must survive the DB round-trip unchanged, since
    # duplicate detection depends on this later.
    reloaded_hashes = {f.name: f.file_hash for f in reloaded_files}
    scanned_hashes = {f.name: f.file_hash for f in scanned_files}
    assert reloaded_hashes == scanned_hashes


# ---------------------------------------------------------------------------
# Pipeline 2: Scan → classify → organize → undo
# ---------------------------------------------------------------------------

def test_scan_classify_and_organize_pipeline(tmp_path, monkeypatch):
    """Full pipeline: scan a file -> classify it with AI (mocked) ->
    plan an organization move based on that category -> preview it
    -> apply it -> undo it. Chains Scanner, Classifier, and
    Organizer together, the way a real 'organize my files' run
    would work."""

    (tmp_path / "invoice_march.txt").write_text(
        "Invoice #4521. Total due: $1,250.00. Payment due within 30 days."
    )

    scanner = FileScanner()
    scanned_files = scanner.scan(tmp_path)
    assert len(scanned_files) == 1
    file_info = scanned_files[0]

    monkeypatch.setattr(classifier_module, "generate_response", lambda p: "Invoice")

    category = classifier_module.classify_file(file_info.name)
    assert category == "Invoice"

    destination = tmp_path / "Documents" / category / file_info.name
    action = OrganizationAction(source=file_info.path, destination=destination)

    organizer = Organizer()

    preview_lines = organizer.preview([action])
    assert "invoice_march.txt" in preview_lines[0]
    assert file_info.path.exists()  # preview alone must not move anything

    organizer.apply([action])
    assert action.status == "moved"
    assert not file_info.path.exists()
    assert destination.exists()

    organizer.undo_last()
    assert action.status == "undone"
    assert file_info.path.exists()
    assert not destination.exists()


# ---------------------------------------------------------------------------
# Pipeline 3: Embed → index → save → load → search
# ---------------------------------------------------------------------------

def test_embed_index_save_load_and_search_pipeline(tmp_path, monkeypatch):
    """Full pipeline: embed some file text (mocked) -> add vectors to
    a real FAISS index -> save the index to disk -> load it back ->
    search it -> confirm the most similar file is found."""

    fake_embeddings = {
        "invoice content":    [1.0, 0.0, 0.0],
        "resume content":     [0.0, 1.0, 0.0],
        "invoice-like query": [0.9, 0.1, 0.0],
    }

    def fake_get_embedding(text, model=None):
        return fake_embeddings[text]

    monkeypatch.setattr(embedder_module, "get_embedding", fake_get_embedding)

    index = SearchIndex(dimension=3)
    index.add("invoice.txt", embedder_module.get_embedding("invoice content"))
    index.add("resume.txt",  embedder_module.get_embedding("resume content"))
    assert len(index) == 2

    index_path = tmp_path / "test_index"
    index.save(index_path)

    assert index_path.with_suffix(".faiss").exists()
    assert index_path.with_suffix(".json").exists()

    reloaded_index = SearchIndex.load(index_path)
    assert len(reloaded_index) == 2

    query_vector = embedder_module.get_embedding("invoice-like query")
    results = reloaded_index.search(query_vector, top_k=1)

    assert len(results) == 1
    top_path, score = results[0]
    assert top_path == "invoice.txt"


# ---------------------------------------------------------------------------
# Pipeline 4: PDF read → embed → index → search
# ---------------------------------------------------------------------------

def test_pdf_to_search_pipeline(tmp_path, monkeypatch):
    """Full pipeline: create a real PDF on disk -> extract its text
    using the PDF reader -> embed the text (mocked) -> add to FAISS
    index -> save/reload index -> search and confirm correct file
    is returned. Proves the document readers feed correctly into
    semantic search."""

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Invoice total due amount payment terms")
    pdf_path = tmp_path / "invoice.pdf"
    doc.save(str(pdf_path))
    doc.close()

    text = read_pdf_text(pdf_path)
    assert text is not None
    assert len(text) > 0

    def fake_get_embedding(text, model=None):
        if any(w in text.lower() for w in ["invoice", "total", "payment"]):
            return [1.0, 0.0, 0.0]
        return [0.0, 1.0, 0.0]

    monkeypatch.setattr(embedder_module, "get_embedding", fake_get_embedding)

    vector = embedder_module.get_embedding(text)
    assert vector is not None

    index = SearchIndex(dimension=3)
    index.add(str(pdf_path), vector)

    idx_path = tmp_path / "pdf_idx"
    index.save(idx_path)
    loaded_index = SearchIndex.load(idx_path)

    query_vector = embedder_module.get_embedding("invoice total due")
    results = loaded_index.search(query_vector, top_k=1)

    assert len(results) == 1
    assert "invoice.pdf" in results[0][0]


# ---------------------------------------------------------------------------
# Pipeline 5: Watcher detects file → suggestion → organize
# ---------------------------------------------------------------------------

def test_watcher_suggestion_to_organize_pipeline(tmp_path, monkeypatch):
    """Full pipeline: a new file appears -> the suggestion engine
    extracts its text, classifies it, and recommends a folder (all
    mocked for AI) -> the organizer applies the suggested move.
    Proves the watcher→suggestion→organizer chain works end-to-end."""

    invoice_file = tmp_path / "invoice_april.txt"
    invoice_file.write_text(
        "Invoice #9821. Total due: $3,750.00. Payment due within 15 days."
    )

    monkeypatch.setattr(classifier_module, "generate_response", lambda p: "Invoice")
    monkeypatch.setattr(recommender_module, "generate_response",
                        lambda p: "Documents/Invoices")

    suggestion = build_suggestion(invoice_file)

    assert suggestion.path == invoice_file
    assert suggestion.category == "Invoice"
    assert suggestion.suggested_folder == "Documents/Invoices"
    assert suggestion.detected_at is not None

    destination = tmp_path / suggestion.suggested_folder / invoice_file.name
    action = OrganizationAction(source=invoice_file, destination=destination)

    organizer = Organizer()
    organizer.apply([action])

    assert action.status == "moved"
    assert destination.exists()
    assert not invoice_file.exists()


# ---------------------------------------------------------------------------
# Pipeline 6: Scan → DB round-trip → detected_type preserved
# ---------------------------------------------------------------------------

def test_detected_type_survives_database_roundtrip(tmp_path):
    """Full pipeline: scan real files with detectable types (JPEG,
    PDF) -> save to database -> reload -> confirm detected_type is
    identical after the round-trip. Proves file-type metadata isn't
    lost when persisted to SQLite."""

    jpeg_path = tmp_path / "photo.jpg"
    jpeg_path.write_bytes(bytes.fromhex("FFD8FFE0") + b"0" * 20)

    doc = fitz.open()
    doc.new_page()
    doc.save(str(tmp_path / "document.pdf"))
    doc.close()

    scanner = FileScanner()
    scanned_files = scanner.scan(tmp_path)
    assert len(scanned_files) == 2

    types_before = {f.name: f.detected_type for f in scanned_files}
    assert types_before["photo.jpg"] == "image/jpeg"
    assert types_before["document.pdf"] == "application/pdf"

    db = DatabaseManager(tmp_path / "test_types.db")
    db.connect()
    for f in scanned_files:
        db.save_file(f)
    reloaded = db.load_files()
    db.close()

    types_after = {f.name: f.detected_type for f in reloaded}
    assert types_before == types_after