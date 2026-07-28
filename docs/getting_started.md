# 🚀 Getting Started with Desktop-AI

Welcome! This guide will help you set up Desktop-AI in 10 minutes and start organizing your files.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation (5 minutes)](#installation-5-minutes)
- [First Run](#first-run)
- [Core Workflow](#core-workflow)
- [Next Steps](#next-steps)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, make sure you have:

| Requirement        | How to Check                              |
| ------------------ | ----------------------------------------- |
| **Python 3.13+**   | `python --version`                        |
| **Ollama**         | [Download](https://ollama.ai) and install |
| **Git (optional)** | `git --version`                           |
| **4GB+ RAM**       | Check system settings                     |

### Install Ollama

Desktop-AI needs Ollama running locally for AI features:

1. Visit [ollama.ai](https://ollama.ai)
2. Download for your OS (Windows, macOS, Linux)
3. Install and launch Ollama
4. It will run as a background service

---

## Installation (5 minutes)

### Step 1: Clone the Repository

```bash
git clone https://github.com/gokul-prof-ai/Desktop-AI.git
cd Desktop-AI
```

Or download as ZIP from GitHub.

### Step 2: Create Virtual Environment

```bash
# Create environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (macOS/Linux)
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This will take 2-3 minutes the first time.

### Step 4: Verify Installation

```bash
# Check imports work
python -c "import src; print('✅ Installation successful!')"

# See installed packages
pip list | grep ollama
```

---

## First Run

### Step 1: Start Ollama

```bash
# Make sure Ollama is running
ollama serve

# In another terminal, check it's accessible
ollama list
```

You should see available models.

### Step 2: Pull a Model

```bash
# Pull Mistral model (recommended for beginners)
ollama pull mistral

# Or try smaller/faster models:
ollama pull neural-chat
ollama pull zephyr
```

This downloads ~7GB the first time. It's one-time only.

### Step 3: Launch Desktop-AI

```bash
# From Desktop-AI folder, with venv activated
python -m src.main
```

You should see:

```
✅ Ollama connection: OK
✅ Database initialized
✅ Server starting on http://localhost:5000
```

### Step 4: Open the Interface

The GUI opens automatically. If not:

1. Open your browser
2. Go to: `http://localhost:5000`
3. You should see the Dashboard

---

## Core Workflow

### 1. Scan Your Files

**What it does:** Analyzes your file system, extracts metadata, creates a database.

```bash
# Via GUI:
# 1. Click "Scan" in the left menu
# 2. Select a folder
# 3. Set max depth (5 is good for most uses)
# 4. Click "Start Scan"

# Via CLI:
python -c "
from src.scanner import FileScanner
scanner = FileScanner('~/Downloads', max_depth=3)
results = scanner.scan()
print(f'Found {len(results)} files')
"
```

**Time estimate:** ~10,000 files/second

### 2. Let AI Classify Files

**What it does:** Uses Ollama to categorize files intelligently.

```bash
# Via GUI:
# 1. Scan a folder
# 2. Click "Analyze" button
# 3. Wait for AI classification
# 4. See suggested categories

# Example output:
# report.pdf -> Category: Documents
# photo.jpg -> Category: Media
# script.py -> Category: Code
```

### 3. Preview Organization

**What it does:** Shows you what will move where before doing anything.

```bash
# Via GUI:
# 1. Click "Organize" after analysis
# 2. Review the proposed changes
# 3. Use checkboxes to select which files to move
# 4. Click "Preview" to see final state
```

### 4. Organize Your Files

**What it does:** Moves files to their recommended folders.

```bash
# Via GUI:
# 1. After preview, click "Apply Changes"
# 2. Confirm in the dialog
# 3. Monitor progress bar
# 4. Review results

# Undo if needed:
# Click "Undo" to revert all changes
```

---

## Next Steps

### 🎓 Learn Core Features

1. **File Scanning** — Organize existing files
2. **Real-Time Watcher** — Auto-organize new downloads
3. **Semantic Search** — Find files by meaning
4. **Smart Folders** — Auto-create organization system

### 📚 Read Documentation

| Guide                                   | Topic               |
| --------------------------------------- | ------------------- |
| [User Guide](./user-guide.md)           | Feature walkthrough |
| [Architecture](./architecture.md)       | How it works        |
| [Configuration](./configuration.md)     | Customization       |
| [Troubleshooting](./troubleshooting.md) | Common issues       |

### 🔧 Customize Settings

```json
// Edit config/default_config.json
{
  "scanner": {
    "max_depth": 5,
    "batch_size": 1000
  },
  "ai": {
    "model": "mistral",
    "temperature": 0.7
  },
  "watcher": {
    "monitored_folders": ["Downloads", "Desktop"]
  }
}
```

See [Configuration Guide](./configuration.md) for all options.

### 🚀 Try Advanced Features

Once comfortable:

- Enable folder watching for automatic organization
- Use semantic search to find files by meaning
- Create custom classification categories
- Export organized file structure

---

## Tips for Success

### ✅ Best Practices

1. **Start small** — Scan a single folder first (Downloads)
2. **Review always** — Always preview before applying changes
3. **Keep backups** — Create a backup folder, "~/.backup"
4. **Test models** — Try different Ollama models
5. **Monitor logs** — Check logs when something seems off

### 🎯 Common First-Time Tasks

#### Task 1: Organize Downloads

```
1. Open Desktop-AI
2. Click "Scan"
3. Select ~/Downloads
4. Set max_depth to 3
5. Wait for scan (~30s for 1000 files)
6. Click "Analyze" for AI classification
7. Click "Organize" to preview changes
8. Click "Apply" to organize
9. Files are now sorted by type!
```

**Result:** Your Downloads folder is clean and organized.

#### Task 2: Set Up Automatic Watching

```
1. Go to Settings
2. Enable "Folder Watcher"
3. Select folders: Downloads, Desktop
4. Set organization frequency (hourly recommended)
5. New files auto-organize as they arrive!
```

**Result:** Automatic organization as you download files.

#### Task 3: Find Files by Meaning

```
1. Go to Search
2. Type natural language query: "photos from summer"
3. AI finds semantically similar files
4. No keyword matching needed!
```

**Result:** Intuitive file discovery.

---

## System Requirements

### Minimum

- Python 3.13+
- 4GB RAM
- 2GB disk space
- Windows 10, macOS 10.14+, Ubuntu 20.04+

### Recommended

- Python 3.13+
- 8GB+ RAM
- GPU (NVIDIA CUDA, Apple Silicon, AMD)
- SSD (for faster scanning)
- 10GB disk space

### Performance Expectations

| Operation         | Time (1000 files) |
| ----------------- | ----------------- |
| Scanning          | ~0.1s             |
| AI Classification | ~5-10s            |
| Semantic Search   | <100ms            |
| Organization      | ~1-2s             |

---

## Troubleshooting

### Ollama Not Found

**Problem:** Error: "Cannot connect to Ollama"

**Solution:**

```bash
# Make sure Ollama is running
ollama serve

# Check connection
curl http://localhost:11434/api/tags

# Verify model exists
ollama list
```

### Port Already in Use

**Problem:** "Port 5000 already in use"

**Solution:**

```bash
# Use different port
export PORT=5001
python -m src.main

# Or kill process using port 5000
lsof -ti:5000 | xargs kill -9  # macOS/Linux
netstat -ano | findstr :5000   # Windows
```

### Slow Performance

**Problem:** Scanning or AI is very slow

**Solution:**

1. Reduce `max_depth` in config
2. Use faster model: `neural-chat` instead of `mistral`
3. Reduce `batch_size` if system gets overloaded
4. Check if antivirus is slowing disk access

### Database Errors

**Problem:** "Database locked" or "I/O error"

**Solution:**

1. Close all Desktop-AI instances
2. Delete `data/desktop_ai.db`
3. Restart application (it recreates database)

### Model Takes Forever to Download

**Problem:** Model download stuck or very slow

**Solution:**

```bash
# Try smaller model
ollama pull neural-chat  # Smaller: ~2GB
ollama pull zephyr       # Fast: ~4GB

# Or manually pull
ollama pull mistral  # Full: ~7GB
```

**[More help in Troubleshooting Guide →](./troubleshooting.md)**

---

## Key Concepts

### File Scanning

Recursively analyzes directories, extracting:

- File metadata (size, date modified)
- File type (from content, not extension)
- SHA-256 hash (for duplicate detection)
- Basic text content

### AI Classification

Uses local LLM to:

- Categorize files intelligently
- Suggest organization
- Generate summaries
- Answer file-related questions

### File Organization

Safely moves files:

- Preview before applying
- Full undo capability
- Preserves file metadata
- Handles duplicates

### Semantic Search

Finds files by meaning:

- "Photos from summer" → Finds images from June-August
- "Tax documents 2024" → Finds all 2024 tax files
- "Project presentations" → Finds all related presentations

---

## Next: Read User Guide

Once you're comfortable with the basics, read the [User Guide](./user-guide.md) to learn:

- Advanced features
- Configuration options
- Workflow optimization
- Keyboard shortcuts

---

<div align="center">

**Ready to organize?** 🎉

[User Guide →](./user-guide.md) •
[Configuration →](./configuration.md) •
[Troubleshooting →](./troubleshooting.md) •
[Back to README ↑](../README.md)

</div>
