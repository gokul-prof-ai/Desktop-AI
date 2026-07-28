# 📋 Documentation Templates Guide

This guide provides ready-to-use templates for the remaining documentation files. Copy and customize as needed.

---

## 1. docs/faq.md Template

````markdown
# ❓ Frequently Asked Questions

## Table of Contents

- [Installation & Setup](#installation--setup)
- [Usage & Features](#usage--features)
- [Performance](#performance)
- [Privacy & Security](#privacy--security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

---

## Installation & Setup

<details>
<summary><b>Q: What are the system requirements?</b></summary>

**A:**

- Python 3.13 or higher
- 4GB RAM minimum (8GB recommended)
- 2GB disk space for application + model
- Windows 10+, Linux, or macOS
- Ollama installed and running

See [Installation Guide](./getting-started.md#prerequisites) for detailed requirements.

</details>

<details>
<summary><b>Q: Do I need an internet connection?</b></summary>

**A:** Not after initial setup. Everything runs locally:

- Files stay on your machine
- AI processing is local
- No cloud dependency
- Completely offline capable

Internet only needed for:

- Initial Python/dependency installation
- Downloading Ollama models (one-time)
- GitHub updates (optional)

</details>

<details>
<summary><b>Q: Can I use it on Linux/macOS?</b></summary>

**A:** Yes, the core library works on all platforms. Current status:

- **Windows:** Full support (GUI + CLI)
- **Linux:** Full support (CLI, GUI in progress)
- **macOS:** Full support (CLI, GUI in progress)

[Roadmap →](./roadmap.md)

</details>

<details>
<summary><b>Q: How do I uninstall Desktop-AI?</b></summary>

**A:** Simple cleanup:

```bash
# Delete the project folder
rm -rf Desktop-AI

# Delete the database (optional)
rm -rf ~/.desktop-ai/data

# Remove virtual environment
rm -rf venv
```
````

That's it! No system-wide installation to remove.

</details>

---

## Usage & Features

<details>
<summary><b>Q: Does organizing files modify them?</b></summary>

**A:** No, Desktop-AI is non-destructive:

- Files keep their original names and content
- Only the folder location changes
- **Preview first:** Always see changes before applying
- **Undo always available:** Revert any operation instantly
- Your data is never deleted or corrupted

</details>

<details>
<summary><b>Q: Which AI models are supported?</b></summary>

**A:** Any Ollama model works! Popular choices:

| Model       | Speed     | Quality   | Size |
| ----------- | --------- | --------- | ---- |
| Mistral     | Medium    | Excellent | 7GB  |
| Neural Chat | Fast      | Good      | 4GB  |
| Zephyr      | Fast      | Very Good | 4GB  |
| Llama 2     | Slow      | Excellent | 7GB  |
| Phi         | Very Fast | Good      | 3GB  |

[How to change models →](./configuration.md#ai-settings)

</details>

<details>
<summary><b>Q: Can I organize other people's files?</b></summary>

**A:** You can analyze any folder you have permission to read. For organizing (moving files), you need write permissions in that folder.

For shared folders:

- Scan and analyze freely
- Ask folder owner before organizing
- Test with a small subset first

</details>

<details>
<summary><b>Q: How do I handle duplicate files?</b></summary>

**A:** Desktop-AI detects duplicates by file hash:

1. **During scanning:** Duplicates are flagged
2. **In the organizer:** Duplicates get special treatment
3. **Options:**
   - Keep first, remove duplicates
   - Move duplicates to separate "Duplicates" folder
   - Manual review before deletion

[Duplicate handling guide →](./user-guide.md#managing-duplicates)

</details>

---

## Performance

<details>
<summary><b>Q: Why is file scanning slow?</b></summary>

**A:** Scanning speed depends on several factors:

| Factor          | Impact               | Solution                |
| --------------- | -------------------- | ----------------------- |
| Folder size     | Large trees = slower | Reduce max_depth        |
| Disk type       | HDD < SSD            | Use SSD if possible     |
| Max depth       | Deeper = slower      | Set to 3-5 typically    |
| Text extraction | Heavy                | Disable for large files |

[Performance tuning →](./configuration.md#performance)

</details>

<details>
<summary><b>Q: How can I speed up AI classification?</b></summary>

**A:** Several ways to improve speed:

1. **Use faster models:**

   ```
   neural-chat (4GB, fastest)
   zephyr (4GB, fast)
   ```

2. **Reduce batch size** for lower memory usage

3. **Enable GPU:** If you have CUDA or Metal

4. **Disable text extraction** for non-document files

[GPU setup guide →](./configuration.md#gpu-support)

</details>

<details>
<summary><b>Q: How much disk space do I need?</b></summary>

**A:** Space breakdown:

- **Desktop-AI app:** ~100MB
- **Ollama models:** 2-13GB (choose one)
- **Your files:** Whatever you're organizing
- **Database:** ~1GB per 10M files
- **Vector index:** ~2GB per 1M files

Total: Plan for ~10-20GB depending on your data.

</details>

---

## Privacy & Security

<details>
<summary><b>Q: Is my data private?</b></summary>

**A:** Yes, completely:

- ✅ All processing happens locally
- ✅ No cloud uploads
- ✅ No telemetry
- ✅ No tracking
- ✅ You have full control

Your files never leave your computer.

</details>

<details>
<summary><b>Q: What data is stored?</b></summary>

**A:** Desktop-AI stores only on your machine:

1. **File metadata:** Path, size, type, date
2. **Classifications:** AI categories and scores
3. **Organization history:** For undo capability
4. **Vector embeddings:** For semantic search
5. **Your config:** User preferences

**Never collected:**

- File contents (except text extraction)
- Usage analytics
- Telemetry data
- Personal information

[Full privacy details →](./architecture.md#security)

</details>

<details>
<summary><b>Q: Is it safe to move important files?</b></summary>

**A:** Yes, with precautions:

1. **Create backup first:**

   ```bash
   # Backup important folder
   cp -r ~/Documents ~/Documents.backup
   ```

2. **Always preview:** Check changes before applying

3. **Use undo:** If something's wrong, undo instantly

4. **Start small:** Test with less important files first

5. **Keep database:** Never delete `data/desktop_ai.db` until you undo

</details>

---

## Troubleshooting

<details>
<summary><b>Q: "Cannot connect to Ollama" error</b></summary>

**A:** Ollama is not running or not accessible:

```bash
# Check if Ollama is running
ollama list

# If error, start Ollama
ollama serve

# Check connection
curl http://localhost:11434/api/tags
```

If still failing:

- Restart Ollama service
- Check firewall settings
- Verify port 11434 is not blocked

[Full troubleshooting →](./troubleshooting.md#ollama-connection-error)

</details>

<details>
<summary><b>Q: "Port 5000 already in use" error</b></summary>

**A:** Something else is using that port:

```bash
# Find what's using port 5000
lsof -i :5000  # macOS/Linux
netstat -ano | findstr :5000  # Windows

# Kill the process or use different port
export PORT=5001
python -m src.main
```

[More solutions →](./troubleshooting.md#port-already-in-use)

</details>

<details>
<summary><b>Q: "Database locked" error</b></summary>

**A:** Multiple instances running simultaneously:

```bash
# Check running instances
ps aux | grep src.main

# Close all instances, then restart
python -m src.main
```

Or database file corruption:

```bash
# Backup old database
mv data/desktop_ai.db data/desktop_ai.db.bak

# Restart (creates new database)
python -m src.main
```

</details>

---

## Contributing

<details>
<summary><b>Q: How can I contribute?</b></summary>

**A:** We welcome contributions! See [Contributing Guide](../CONTRIBUTING.md) for:

- Bug reports
- Feature implementations
- Documentation improvements
- Test additions
- Code review

Start with [existing issues](https://github.com/gokul-prof-ai/Desktop-AI/issues).

</details>

<details>
<summary><b>Q: What should I work on?</b></summary>

**A:** Good first contributions:

- 🐛 Bug fixes (labeled "good first issue")
- 📚 Documentation improvements
- 🧪 Adding tests
- 🎨 UI enhancements

Check the [roadmap](./roadmap.md) for planned features.

</details>

---

## Still Have Questions?

- 📖 [Full Documentation](../README.md#-documentation)
- 💬 [GitHub Discussions](https://github.com/gokul-prof-ai/Desktop-AI/discussions)
- 📧 Email: gokul3krish2@gmail.com
- 🐛 [Report Issues](https://github.com/gokul-prof-ai/Desktop-AI/issues)

---

````

---

## 2. docs/configuration.md Template

```markdown
# ⚙️ Configuration Guide

Configuration controls Desktop-AI behavior. This guide explains all options.

## Table of Contents

- [Configuration File Location](#configuration-file-location)
- [Scanner Settings](#scanner-settings)
- [AI Settings](#ai-settings)
- [Database Settings](#database-settings)
- [Watcher Settings](#watcher-settings)
- [UI Settings](#ui-settings)
- [Environment Variables](#environment-variables)
- [Performance Tuning](#performance-tuning)
- [Examples](#examples)

---

## Configuration File Location

Desktop-AI looks for configuration in this order:

1. Environment variable: `DESKTOP_AI_CONFIG`
2. Current directory: `./config/config.json`
3. User home: `~/.config/desktop-ai/config.json`
4. Default: `config/default_config.json`

**Edit your configuration:**

```bash
# Windows
notepad config\default_config.json

# macOS/Linux
nano config/default_config.json
````

---

## Scanner Settings

```json
{
  "scanner": {
    "max_depth": 5,
    "ignored_extensions": [".tmp", ".cache", ".bak"],
    "ignored_folders": ["node_modules", ".git", "__pycache__"],
    "batch_size": 1000,
    "extract_text": true,
    "text_preview_length": 500
  }
}
```

| Setting               | Type  | Default   | Description                    |
| --------------------- | ----- | --------- | ------------------------------ |
| `max_depth`           | int   | 5         | Maximum folder recursion depth |
| `ignored_extensions`  | array | See above | File extensions to skip        |
| `ignored_folders`     | array | See above | Folder names to skip           |
| `batch_size`          | int   | 1000      | Files processed per batch      |
| `extract_text`        | bool  | true      | Extract text from documents    |
| `text_preview_length` | int   | 500       | Characters to extract          |

---

## AI Settings

```json
{
  "ai": {
    "enabled": true,
    "model": "mistral",
    "base_url": "http://localhost:11434",
    "temperature": 0.7,
    "timeout": 30,
    "cache_classifications": true
  }
}
```

| Setting                 | Type   | Default                  | Description              |
| ----------------------- | ------ | ------------------------ | ------------------------ |
| `enabled`               | bool   | true                     | Enable AI features       |
| `model`                 | string | "mistral"                | Ollama model name        |
| `base_url`              | string | "http://localhost:11434" | Ollama API URL           |
| `temperature`           | float  | 0.7                      | AI creativity (0.0-1.0)  |
| `timeout`               | int    | 30                       | Response timeout seconds |
| `cache_classifications` | bool   | true                     | Cache AI results         |

**Available Models:**

- `mistral` — Balanced (recommended)
- `neural-chat` — Fast
- `zephyr` — Quality
- `llama2` — Large model
- `phi` — Tiny

---

## Database Settings

```json
{
  "database": {
    "path": "data/desktop_ai.db",
    "backup_enabled": true,
    "backup_interval": 3600,
    "cleanup_old_operations": true,
    "cleanup_days": 30
  }
}
```

| Setting                  | Type   | Default              | Description             |
| ------------------------ | ------ | -------------------- | ----------------------- |
| `path`                   | string | "data/desktop_ai.db" | Database file location  |
| `backup_enabled`         | bool   | true                 | Automatic backups       |
| `backup_interval`        | int    | 3600                 | Backup interval seconds |
| `cleanup_old_operations` | bool   | true                 | Remove old history      |
| `cleanup_days`           | int    | 30                   | Days to keep history    |

---

## Watcher Settings

```json
{
  "watcher": {
    "enabled": true,
    "monitored_folders": ["Downloads", "Desktop"],
    "poll_interval": 2,
    "auto_organize": false,
    "auto_organize_interval": 3600
  }
}
```

| Setting                  | Type  | Default   | Description             |
| ------------------------ | ----- | --------- | ----------------------- |
| `enabled`                | bool  | true      | Enable folder watching  |
| `monitored_folders`      | array | See above | Folders to watch        |
| `poll_interval`          | int   | 2         | Check interval seconds  |
| `auto_organize`          | bool  | false     | Auto-organize new files |
| `auto_organize_interval` | int   | 3600      | Organization interval   |

---

## UI Settings

```json
{
  "ui": {
    "theme": "dark",
    "port": 5000,
    "language": "en",
    "show_tips": true
  }
}
```

| Setting     | Type   | Default | Description           |
| ----------- | ------ | ------- | --------------------- |
| `theme`     | string | "dark"  | UI theme (dark/light) |
| `port`      | int    | 5000    | Web UI port           |
| `language`  | string | "en"    | UI language           |
| `show_tips` | bool   | true    | Show helpful tips     |

---

## Environment Variables

Set via environment or `.env` file:

```bash
# Database location
export DESKTOP_AI_DB_PATH=/custom/path/db.sqlite

# Ollama settings
export OLLAMA_MODEL=mistral
export OLLAMA_BASE_URL=http://localhost:11434

# UI settings
export DESKTOP_AI_PORT=5000
export DESKTOP_AI_THEME=dark

# Logging
export DESKTOP_AI_LOG_LEVEL=INFO
```

---

## Performance Tuning

### For Slower Systems (4GB RAM, HDD)

```json
{
  "scanner": {
    "max_depth": 3,
    "batch_size": 500
  },
  "ai": {
    "model": "phi",
    "temperature": 0.5
  }
}
```

### For Faster Systems (16GB RAM, SSD, GPU)

```json
{
  "scanner": {
    "max_depth": 10,
    "batch_size": 5000
  },
  "ai": {
    "model": "mistral",
    "temperature": 0.9
  },
  "watcher": {
    "auto_organize": true
  }
}
```

### GPU Support (if available)

For NVIDIA CUDA:

```bash
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_RUNNER=cuda
```

For Apple Silicon:

```bash
# Automatic (Metal support built-in)
```

For AMD ROCM:

```bash
export ROCM_HOME=/opt/rocm
```

---

## Examples

### Example 1: Conservative Setup (Slow System)

```json
{
  "scanner": {
    "max_depth": 3,
    "batch_size": 500,
    "extract_text": false
  },
  "ai": {
    "model": "neural-chat",
    "temperature": 0.5,
    "cache_classifications": true
  },
  "watcher": {
    "enabled": false
  }
}
```

### Example 2: Aggressive Setup (Fast System)

```json
{
  "scanner": {
    "max_depth": 10,
    "batch_size": 2000,
    "extract_text": true
  },
  "ai": {
    "model": "mistral",
    "temperature": 0.8,
    "cache_classifications": true
  },
  "watcher": {
    "enabled": true,
    "auto_organize": true,
    "auto_organize_interval": 300
  }
}
```

---

## Reset to Defaults

```bash
# Restore default configuration
cp config/default_config.json config/config.json

# Or delete to use built-in defaults
rm config/config.json
```

---

## Advanced Configuration

### Custom File Extraction

```json
{
  "document_reader": {
    "pdf": {
      "extract_images": true,
      "ocr_enabled": true
    },
    "office": {
      "extract_formatting": false
    }
  }
}
```

### Custom Categories

```json
{
  "categories": {
    "documents": ["pdf", "docx", "txt"],
    "media": ["jpg", "png", "mp4"],
    "code": ["py", "js", "java"]
  }
}
```

---

## Troubleshooting Configuration

**Invalid JSON:** Check syntax at [jsonlint.com](https://jsonlint.com)

**Settings not applying:** Restart application after changes

**Performance issues:** See [Performance Tuning](#performance-tuning)

---

````

---

## 3. docs/user-guide.md Template

```markdown
# 👤 User Guide

Complete feature walkthrough and usage guide.

## Table of Contents

- [Getting Around](#getting-around)
- [File Scanning](#file-scanning)
- [AI Classification](#ai-classification)
- [File Organization](#file-organization)
- [Searching Files](#searching-files)
- [Folder Watching](#folder-watching)
- [Managing Duplicates](#managing-duplicates)
- [Keyboard Shortcuts](#keyboard-shortcuts)
- [Tips & Tricks](#tips--tricks)

---

## Getting Around

### Dashboard Overview

[Screenshot placeholder]

The dashboard shows:
- **Recent Activity:** Latest file operations
- **Statistics:** File counts, storage usage
- **Quick Actions:** Common tasks
- **Alerts:** Issues that need attention

### Main Menu

- 🏠 **Home:** Dashboard
- 📂 **Scanner:** Scan folders
- 🤖 **Analyzer:** AI classification
- 📋 **Organizer:** File organization
- 🔍 **Search:** Find files
- ⚙️ **Settings:** Configuration

---

## File Scanning

### Starting a Scan

1. Click **Scanner** in main menu
2. Click **Select Folder**
3. Choose the folder to scan
4. Set options:
   - **Max Depth:** How deep to recurse (5 = most folders)
   - **Extract Text:** Read file contents
5. Click **Start Scan**

### Understanding Scan Results

[Results table description]

- ✅ Total Files: Files found
- 📊 File Types: Breakdown by type
- 🔍 Duplicates Found: Hash-based detection
- ⏱️ Scan Time: Duration in seconds

### Large Folder Scanning

For very large folders:
1. Reduce `max_depth`
2. Ignore unnecessary folders
3. Disable text extraction
4. Process in batches

---

## AI Classification

### Running Classification

1. After scanning, click **Analyzer**
2. Click **Analyze Files**
3. Wait for AI processing
4. Review suggested categories

### Understanding Classifications

Each file gets:
- **Category:** Suggested folder
- **Confidence:** How sure (0-100%)
- **Reason:** Why it was categorized

### Adjusting Classifications

- Edit categories manually
- Retrain with feedback (planned)
- Use custom rules

---

## File Organization

### Organization Workflow

1. **Scan** files
2. **Analyze** with AI
3. **Preview** changes
4. **Review** proposed moves
5. **Apply** when ready
6. **Undo** if needed

### Previewing Changes

Before organizing:
1. Click **Organize**
2. Review proposed changes
3. Uncheck any files to keep
4. Check folder destinations
5. Click **Preview** to see result

### Applying Changes

1. Click **Apply Changes**
2. Confirm in dialog
3. Monitor progress
4. Review results

---

## Searching Files

### Semantic Search

Find files by meaning:
- "Photos from summer" → June-August images
- "2024 taxes" → All tax documents
- "Project presentations" → Related files

[Search interface screenshot]

### Advanced Filters

Combine search with filters:
- **Date:** Before/After specific date
- **Size:** Minimum/Maximum file size
- **Type:** Specific file types
- **Tags:** Custom tags

---

## Folder Watching

### Enabling Folder Watch

1. Go to **Settings**
2. Enable **Folder Watcher**
3. Select folders to watch
4. Configure behavior:
   - **Auto-organize:** Automatic or manual
   - **Interval:** How often to check

### What Folder Watch Does

- Monitors specified folders
- Detects new files
- Suggests organization
- Optional auto-organization

---

## Managing Duplicates

### Finding Duplicates

1. After scanning, click **Duplicates**
2. View all duplicate groups
3. Files grouped by hash

### Handling Duplicates

Options for each group:
- **Keep First:** Remove others
- **Keep Largest:** Remove smaller
- **Move to Folder:** Separate location
- **Delete:** Permanently remove

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Start new scan |
| `Ctrl+F` | Open search |
| `Ctrl+Z` | Undo last action |
| `Ctrl+,` | Open settings |
| `F5` | Refresh view |
| `?` | Show help |

---

## Tips & Tricks

### Tip 1: Use Previews
Always preview before applying changes!

### Tip 2: Start Small
Test with Downloads folder first.

### Tip 3: Save Searches
Save common searches for reuse.

### Tip 4: Regular Backups
Backup important folders before organizing.

### Tip 5: Monitor Performance
Check logs if things seem slow.

---
````

---

## 4. docs/roadmap.md Template

```markdown
# 🗺️ Project Roadmap

Overview of completed work and future plans.

## Legend

- ✅ Completed
- 🚀 In Progress
- 📋 Planned
- ❌ Blocked

---

## Current Status

**Phase:** 8/14 - Folder Watcher Complete
**Stability:** Production Ready (Beta)
**Test Coverage:** 69+ unit tests

---

## Completed Phases ✅

### Phase 1-3: Foundation (✅ Complete)

- [x] Project planning and architecture
- [x] Development environment setup
- [x] File scanner with recursion
- [x] Depth limiting and filtering

### Phase 4-5: Data Management (✅ Complete)

- [x] File hashing (SHA-256)
- [x] File type detection from content
- [x] SQLite database schema
- [x] Centralized logging system

### Phase 6-8: Document Processing (✅ Complete)

- [x] PDF text extraction
- [x] DOCX parsing
- [x] Excel reading
- [x] OCR for scanned images

### Phase 9: AI Integration (✅ Complete)

- [x] Ollama integration
- [x] File classification
- [x] Summarization
- [x] Folder recommendations
- [x] Response caching

### Phase 10: File Organization (✅ Complete)

- [x] Organization engine
- [x] Preview before changes
- [x] Full undo support
- [x] Duplicate detection

### Phase 11: Real-Time Monitoring (✅ Complete)

- [x] Folder watcher
- [x] Event detection
- [x] AI suggestions
- [x] Auto-organization (optional)

### Phase 12: Semantic Search (✅ Complete)

- [x] FAISS integration
- [x] Vector embeddings
- [x] Semantic search
- [x] Hybrid search

### Phase 13: Desktop GUI (✅ Complete)

- [x] PySide6 Qt application
- [x] Dashboard
- [x] File manager interface
- [x] Search UI
- [x] Settings panel
- [x] AI chat interface

### Phase 14: Unit Tests (✅ Complete)

- [x] Scanner tests
- [x] AI integration tests
- [x] Database tests
- [x] File organizer tests
- [x] 69+ total tests

---

## In Progress 🚀

### Integration Testing

- [ ] End-to-end pipeline tests
- [ ] User workflow tests
- [ ] Performance benchmarks
- [ ] Stress testing

### Performance Optimization

- [ ] Database query optimization
- [ ] Caching strategies
- [ ] Parallel processing
- [ ] Memory optimization

### Cross-Platform Support

- [ ] Linux full support
- [ ] macOS full support
- [ ] Windows optimizations

---

## Planned Features 📋

### Phase 15: Advanced Memory

- [ ] Learn user preferences
- [ ] Remember folder choices
- [ ] Pattern recognition
- [ ] Adaptive suggestions

### Phase 16: AI Planner

- [ ] Multi-step task planning
- [ ] Batch operations
- [ ] Custom workflows
- [ ] Scheduled tasks

### Phase 17: Release & Distribution

- [ ] PyPI package
- [ ] Installer creation
- [ ] Version management
- [ ] Auto-updates

### Phase 18: Voice Support

- [ ] Voice input recognition
- [ ] Voice commands
- [ ] Voice feedback
- [ ] Natural language processing

### Phase 19: Advanced Features

- [ ] Duplicate removal
- [ ] Large file detection
- [ ] Empty folder cleanup
- [ ] Automated archival

---

## Known Issues ❌

| Issue       | Status      | Notes                   |
| ----------- | ----------- | ----------------------- |
| Linux GUI   | Blocked     | Qt compatibility issues |
| macOS M1    | In Progress | Native support coming   |
| Large files | Workaround  | Set max_depth lower     |

---

## Timeline

- **Q1 2024:** Current (Phases 1-14)
- **Q2 2024:** Integration testing, optimization
- **Q3 2024:** v1.0 release
- **Q4 2024:** Advanced features

---

## How to Contribute

See [Contributing Guide](../CONTRIBUTING.md) to:

- Pick an issue to work on
- Submit improvements
- Report bugs
- Suggest features

---
```

---

## How to Use These Templates

1. Copy the content above
2. Create the corresponding file: `docs/filename.md`
3. Customize with your specific information
4. Add screenshots/examples where indicated
5. Test links and formatting
6. Commit to repository

---

## Customization Tips

### For FAQ

- Add real questions you've received
- Update model names if different
- Adjust paths to match your setup
- Add industry-specific questions

### For Configuration

- Document your actual config schema
- Add examples for your use cases
- Include performance presets
- Document any custom settings

### For User Guide

- Add screenshots of your UI
- Include keyboard shortcuts
- Add workflow diagrams
- Highlight your unique features

### For Roadmap

- Use actual version numbers
- Set realistic timelines
- Link to issues/PRs
- Update regularly

---

<div align="center">

**Ready to fill in the templates?**

[Back to Summary →](./DOCUMENTATION_SUMMARY.md)

</div>
