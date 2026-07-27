# Testing Guide

## Test Structure

\`\`\`
tests/
├── conftest.py # Shared fixtures
├── test_scanner.py # 8 tests
├── test_database.py # 6 tests
├── test_organizer.py # 8 tests
├── test_search_engine.py # 10 tests
├── test_integration.py # 12 tests
└── test_performance.py # 4 tests
\`\`\`

## Test Categories

### Unit Tests

Test individual functions in isolation

### Integration Tests

Test module interactions

### Performance Tests

Ensure performance targets:

- Scanning: 1,000 files/sec
- Search: <200ms for 10K files
- Classification: <500ms per file

## Writing Tests

\`\`\`python
import pytest
from src.scanner import FileScanner

@pytest.fixture
def scanner():
return FileScanner()

def test_scan_empty_folder(scanner, tmp_path):
"""Test scanning empty directory returns empty list."""
result = scanner.scan(str(tmp_path))
assert result == []

def test_scan_with_files(scanner, tmp_path):
"""Test scanning folder with files.""" # Create test files
(tmp_path / "test.txt").write_text("content")

    # Scan
    result = scanner.scan(str(tmp_path))

    # Assert
    assert len(result) == 1
    assert result[0].name == "test.txt"

\`\`\`

## Coverage Targets

- Overall: 80%+
- Core modules (scanner, database, search): 90%+
- UI modules: 70%+

## Running Tests

[Already covered in Development.md]
