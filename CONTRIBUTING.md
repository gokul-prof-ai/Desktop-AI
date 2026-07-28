# 🤝 Contributing to Desktop-AI

Thank you for your interest in contributing to Desktop-AI! This document provides guidelines and instructions for making meaningful contributions to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Code Style Guide](#code-style-guide)
- [Commit Message Guidelines](#commit-message-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Documentation](#documentation)
- [Questions?](#questions)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](./CODE_OF_CONDUCT.md). By participating, you agree to uphold this code. Please report unacceptable behavior to the project maintainers.

**Our Pledge:**

- We are committed to providing a welcoming and inspiring community for all
- We value respectful and constructive dialogue
- We celebrate diversity and inclusion

---

## Ways to Contribute

### 🐛 Report Bugs

Found a bug? Report it on [GitHub Issues](https://github.com/gokul-prof-ai/Desktop-AI/issues) with:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, etc.)

### ✨ Suggest Features

Have an idea? [Open a feature request](https://github.com/gokul-prof-ai/Desktop-AI/issues) with:

- Clear use case
- Expected behavior
- Any relevant examples or references

### 📝 Improve Documentation

- Fix typos or clarify explanations
- Add examples or tutorials
- Improve API documentation
- Create guides for common tasks

### 🔧 Fix Bugs or Add Features

- Pick an [open issue](https://github.com/gokul-prof-ai/Desktop-AI/issues)
- Implement the fix or feature
- Submit a pull request

### 🧪 Improve Tests

- Increase test coverage
- Add integration tests
- Improve test documentation
- Fix flaky tests

---

## Getting Started

### Prerequisites

- **Python:** 3.13+
- **Git:** For version control
- **Ollama:** For AI model testing
- **Text Editor/IDE:** VS Code, PyCharm, etc.

### 1. Fork the Repository

Click the "Fork" button on GitHub to create your own copy.

### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/Desktop-AI.git
cd Desktop-AI
```

### 3. Add Upstream Remote

```bash
git remote add upstream https://github.com/gokul-prof-ai/Desktop-AI.git
git fetch upstream
```

### 4. Create a Branch

```bash
# Update main branch
git checkout main
git pull upstream main

# Create feature branch
git checkout -b fix/issue-123-short-description
# or for features:
git checkout -b feature/amazing-new-feature
```

**Branch naming conventions:**

- `fix/` for bug fixes
- `feature/` for new features
- `docs/` for documentation
- `test/` for tests
- `refactor/` for code improvements

---

## Development Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

### 2. Set Up Git Hooks (Optional but Recommended)

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install
```

### 3. Start Ollama

```bash
# In a separate terminal
ollama serve
ollama pull mistral  # Or your preferred model
```

### 4. Verify Setup

```bash
# Run tests to verify everything works
pytest

# Run the application
python -m src.main
```

---

## Making Changes

### 1. Keep Your Branch Updated

```bash
git fetch upstream
git rebase upstream/main
```

### 2. Make Your Changes

- Follow the [Code Style Guide](#code-style-guide)
- Write clear, descriptive commit messages
- Add or update tests for your changes
- Update documentation if needed

### 3. Test Locally

```bash
# Run all tests
pytest

# Run tests for specific module
pytest tests/test_scanner.py

# Run with coverage
pytest --cov=src tests/

# Run linting (if available)
black src/ tests/
```

---

## Testing

### Writing Tests

1. **Unit Tests:** Test individual functions/classes
2. **Integration Tests:** Test multiple components together
3. **End-to-End Tests:** Test complete workflows

### Test File Structure

```python
import pytest
from src.module import function_to_test

class TestFunctionName:
    """Test suite for function_to_test"""

    def setup_method(self):
        """Setup before each test"""
        pass

    def teardown_method(self):
        """Cleanup after each test"""
        pass

    def test_success_case(self):
        """Test happy path"""
        result = function_to_test(valid_input)
        assert result == expected_output

    def test_edge_case(self):
        """Test edge cases"""
        result = function_to_test(edge_case_input)
        assert result == expected_output

    def test_error_case(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific file
pytest tests/test_scanner.py

# Run specific test
pytest tests/test_scanner.py::TestScanner::test_recursive_scan

# Run with coverage
pytest --cov=src tests/

# Run with markers
pytest -m unit  # Only unit tests
pytest -m integration  # Only integration tests
```

### Coverage Goals

- Maintain minimum 80% code coverage
- 100% coverage for critical modules (scanner, organizer, ai)
- All new code must include tests

---

## Submitting Changes

### 1. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with meaningful message
git commit -m "Fix: Resolve issue with file scanning depth limit

- Update scanner to properly handle max_depth configuration
- Add unit tests for depth limiting
- Update documentation with examples"
```

See [Commit Message Guidelines](#commit-message-guidelines) for format.

### 2. Push to Your Fork

```bash
git push origin fix/issue-123-short-description
```

### 3. Create a Pull Request

On GitHub, create a PR from your branch to `main` with:

- **Title:** Clear, descriptive title
- **Description:** Reference the issue, explain changes
- **Screenshots:** For UI changes
- **Checklist:** Confirm tests pass, docs updated, etc.

---

## Code Style Guide

### Python Style

Follow [PEP 8](https://pep8.org/) with these preferences:

```python
# Import order
import sys
import os
from typing import Optional, List

# Function signatures
def process_files(
    directory: str,
    max_depth: int = 5,
    ignore_hidden: bool = True
) -> List[str]:
    """
    Process files in a directory.

    Args:
        directory: Path to scan
        max_depth: Maximum recursion depth
        ignore_hidden: Skip hidden files

    Returns:
        List of file paths

    Raises:
        FileNotFoundError: If directory doesn't exist
    """
    pass

# Use type hints
def calculate_checksum(content: bytes) -> str:
    """Calculate SHA-256 checksum."""
    pass

# Constants in UPPER_CASE
MAX_FILE_SIZE = 1024 * 1024 * 100  # 100MB
DEFAULT_BATCH_SIZE = 1000

# Private methods with underscore
def _internal_helper():
    pass
```

### Naming Conventions

```python
# Classes: PascalCase
class FileScanner:
    pass

# Functions/methods: snake_case
def scan_directory():
    pass

# Constants: UPPER_CASE
MAX_DEPTH = 5

# Private: _leading_underscore
def _internal_function():
    pass

# Protected: _leading_underscore
def _protected_method(self):
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def summarize_document(file_path: str, max_length: int = 500) -> str:
    """
    Summarize a document using the local AI model.

    Args:
        file_path: Path to the document file
        max_length: Maximum summary length in characters

    Returns:
        Summary text

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If max_length is invalid

    Examples:
        >>> summary = summarize_document('report.pdf')
        >>> print(summary)
    """
    pass
```

### Comments

```python
# Use comments for "why", not "what"
# Good:
# Skip hidden files to avoid processing system files
if filename.startswith('.'):
    continue

# Bad:
# Skip if starts with dot
if filename.startswith('.'):
    continue
```

---

## Commit Message Guidelines

### Format

```
<type>: <subject>

<body>

<footer>
```

### Types

- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, semicolons, etc.)
- `refactor:` Code refactoring without feature changes
- `test:` Adding or updating tests
- `perf:` Performance improvements
- `chore:` Build, dependencies, tooling

### Subject

- Use imperative, present tense: "Add" not "Added"
- Don't capitalize first letter
- No period (.) at the end
- Limit to 50 characters

### Body

- Explain what and why, not how
- Wrap at 72 characters
- Separate from subject with blank line
- Use bullet points for multiple changes

### Footer

- Reference issues: `Fixes #123`
- Reference PRs: `Related to #456`

### Examples

```
fix: resolve file scanner depth limit issue

The scanner was ignoring the max_depth configuration parameter,
causing unnecessary deep recursion. This fix:
- Properly applies the depth limit during traversal
- Adds validation for the configuration value
- Improves performance for large directory trees

Fixes #42
```

```
docs: add configuration guide with examples

- Expand API documentation with parameter descriptions
- Add code examples for common use cases
- Include troubleshooting section

Relates to #89
```

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guide
- [ ] All tests pass: `pytest`
- [ ] Coverage maintained: `pytest --cov=src`
- [ ] Documentation updated
- [ ] Commit messages follow guidelines
- [ ] No unrelated changes included

### PR Description Template

```markdown
## Description

Brief summary of changes

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issue

Fixes #123

## Testing

- [ ] Unit tests added/updated
- [ ] Manual testing completed
- [ ] Coverage maintained (>80%)

## Checklist

- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally

## Screenshots (if applicable)

Add screenshots for UI changes
```

### Review Process

1. **Automated Checks:** CI/CD pipeline must pass
2. **Code Review:** Maintainers review for:
   - Code quality
   - Test coverage
   - Documentation
   - Performance impact
3. **Approval:** Requires approval from at least one maintainer
4. **Merge:** Squash and merge to keep history clean

---

## Reporting Bugs

### Before Reporting

- Check [existing issues](https://github.com/gokul-prof-ai/Desktop-AI/issues)
- Check [FAQ](./docs/faq.md) and [troubleshooting](./docs/troubleshooting.md)
- Try with the latest version

### Bug Report Template

```markdown
**Describe the bug**
Clear description of what happened

**To Reproduce**
Steps to reproduce the issue:

1. ...
2. ...

**Expected behavior**
What should happen instead

**Actual behavior**
What actually happened

**Environment**

- OS: [Windows 10/Linux/macOS]
- Python: [3.13.x]
- Desktop-AI version: [latest/1.0.0]
- Ollama model: [mistral]

**Error logs**
```

Error message and stack trace

```

**Additional context**
Screenshots, configuration files (sanitized), etc.
```

---

## Suggesting Features

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
Description of the problem

**Describe the solution you'd like**
Clear description of desired feature

**Describe alternatives you've considered**
Other solutions or workarounds

**Additional context**
Examples, use cases, or mockups
```

### Feature Discussion

Before implementing major features, open an issue to discuss:

- Design approach
- Implementation strategy
- Potential impact
- Resource requirements

This prevents wasted effort on features that may not align with the project vision.

---

## Documentation

### Guidelines

1. **Clarity:** Write for users unfamiliar with the codebase
2. **Examples:** Include code examples
3. **Completeness:** Cover all parameters, return values, exceptions
4. **Accuracy:** Keep documentation in sync with code
5. **Organization:** Use clear headings and structure

### What to Document

- **Code:** Docstrings for all public functions/classes
- **Features:** User guides and tutorials
- **API:** Complete parameter and return documentation
- **Examples:** Real-world usage examples
- **Changes:** Update CHANGELOG for significant changes

### Documentation Files

- `README.md` — Project overview and quick start
- `docs/getting-started.md` — Setup and first steps
- `docs/user-guide.md` — Feature documentation
- `docs/architecture.md` — System design
- `docs/api-reference.md` — API documentation
- `CONTRIBUTING.md` — This file
- `CHANGELOG.md` — Version history

---

## Questions?

### Communication Channels

- 💬 **GitHub Issues:** For bugs and features
- 📧 **Email:** gokul3krish2@gmail.com
- 💭 **Discussions:** [GitHub Discussions](https://github.com/gokul-prof-ai/Desktop-AI/discussions)

### Getting Help

1. Check documentation first
2. Search existing issues
3. Ask in GitHub Discussions
4. Email maintainers for detailed questions

---

## Recognition

Contributors are recognized in:

- [README.md](./README.md#credits) — Credits section
- [CHANGELOG.md](./CHANGELOG.md) — Version history
- [GitHub Contributors](https://github.com/gokul-prof-ai/Desktop-AI/graphs/contributors)

Thank you for contributing! 🌟

---

<div align="center">

**Happy Contributing!**

[Back to README ↑](./README.md)

</div>
