# Development Setup & Workflow

## Local Development Environment

### 1. Clone & Setup

\`\`\`bash
git clone https://github.com/gokul-prof-ai/Desktop-AI.git
cd Desktop-AI
python -m venv venv
venv\\Scripts\\activate # Windows
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt # For testing, linting
\`\`\`

### 2. Configuration

Copy `config/config.yaml.example` → `config/config.yaml`

### 3. Run Tests

\`\`\`bash
pytest # Run all tests
pytest -v # Verbose output
pytest --cov # With coverage report
pytest tests/test_scanner.py # Specific test
\`\`\`

## Project Workflow

### Adding a New Feature

1. Create branch: `git checkout -b feature/feature-name`
2. Implement with tests
3. Ensure 80%+ test coverage
4. Follow coding standards (docs/08-CODING_STANDARDS.md)
5. Submit PR with description

### Code Style

- Use Black for formatting
- Use pylint for linting
- Type hints required for public APIs
- Docstrings in Google style

### Testing Requirements

- All public methods must have tests
- Edge cases must be covered
- Integration tests for cross-module flows

## Common Commands

\`\`\`bash

# Format code

black src/ tests/

# Lint code

pylint src/

# Run tests with coverage

pytest --cov=src tests/

# Generate documentation

python scripts/generate_docs.py

# Build application

python scripts/build_app.py
\`\`\`

## IDE Setup

- Recommended: VSCode or PyCharm
- Extensions: Python, Pylance, Black Formatter
- Settings: [.vscode/settings.json example]
