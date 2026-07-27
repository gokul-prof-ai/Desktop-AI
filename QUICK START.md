# Quick Start Guide - Get Running in 5 Minutes

## Prerequisites

- Python 3.13+
- Windows OS (currently)
- 2GB free disk space
- Ollama installed & running

## Installation (2 min)

\`\`\`bash
git clone https://github.com/gokul-prof-ai/Desktop-AI.git
cd Desktop-AI
pip install -r requirements.txt
\`\`\`

## Run Your First Scan (3 min)

\`\`\`bash

# Scan a folder

python src/app.py C:\Users\YourName\Downloads

# Or use environment variable

set DESKTOPAI_SCAN_FOLDER=C:\Users\YourName\Downloads
python src/app.py
\`\`\`

## Next Steps

- Read [Installation Guide](docs/01-INSTALLATION.md) for advanced setup
- Check [User Guide](docs/03-USER_GUIDE.md) for feature walkthrough
- See [Troubleshooting](docs/11-TROUBLESHOOTING.md) if issues arise
