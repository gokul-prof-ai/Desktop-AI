# 📞 Support & Getting Help

Need help with Desktop-AI? You've come to the right place! This guide will help you find answers quickly.

## Table of Contents

- [Quick Self-Help](#quick-self-help)
- [Support Channels](#support-channels)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)
- [Contact](#contact)

---

## 🚀 Quick Self-Help

Before reaching out, try these quick fixes:

### 1. Check Documentation

Start here:

- 📖 [README.md](./README.md) — Overview and quick start
- 🚀 [Getting Started Guide](./docs/getting-started.md) — Setup instructions
- 🔧 [Configuration Guide](./docs/configuration.md) — Settings and customization
- ❓ [FAQ](./docs/faq.md) — Common questions answered
- 🐛 [Troubleshooting Guide](./docs/troubleshooting.md) — Common issues and solutions

### 2. Search Existing Issues

Visit [GitHub Issues](https://github.com/gokul-prof-ai/Desktop-AI/issues) and search for keywords related to your problem. Your issue may already be solved!

### 3. Check Logs

Look in the `logs/` directory for error messages:

```bash
# View latest log file
cat logs/desktop_ai.log | tail -100

# Search for errors
grep ERROR logs/desktop_ai.log

# Check specific module
grep -i "scanner" logs/desktop_ai.log
```

### 4. Test in Isolation

Try to reproduce the issue in a minimal example:

```python
from src.scanner import FileScanner

# Test scanner alone
scanner = FileScanner(directory="test_folder", max_depth=1)
results = scanner.scan()
print(results)
```

---

## 💬 Support Channels

Choose the best channel for your question:

### GitHub Issues (Best for bugs & features)

**Use for:**

- 🐛 Bug reports with reproducible steps
- ✨ Feature requests with use cases
- 📋 Task tracking and accountability

**How to open an issue:**

1. Go to [Issues](https://github.com/gokul-prof-ai/Desktop-AI/issues)
2. Click "New Issue"
3. Choose template (Bug Report or Feature Request)
4. Fill in all details
5. Submit and wait for response (usually within 24-48 hours)

### GitHub Discussions (Best for questions & ideas)

**Use for:**

- ❓ General questions about usage
- 💡 Ideas and suggestions
- 💬 Community discussions
- 📚 Best practices and advice

**How to start a discussion:**

1. Go to [Discussions](https://github.com/gokul-prof-ai/Desktop-AI/discussions)
2. Click "New Discussion"
3. Choose category:
   - `Q&A` — Questions needing answers
   - `Ideas` — Feature ideas and improvements
   - `General` — Off-topic discussion
   - `Announcements` — News and updates
4. Post your question and wait for community response

### Email

**Use for:**

- 🔐 Security concerns
- 📧 Private matters
- 💼 Business inquiries

**Contact:** gokul3krish2@gmail.com

---

## 🔧 Troubleshooting

### Common Issues Quick Reference

| Issue                        | Solution                                 |
| ---------------------------- | ---------------------------------------- |
| **Ollama connection error**  | Ensure Ollama is running: `ollama serve` |
| **Model not found**          | Pull the model: `ollama pull mistral`    |
| **Port 5000 already in use** | Change port in config or kill process    |
| **Files not scanning**       | Check folder permissions                 |
| **GUI won't load**           | Check browser console for errors         |
| **Slow performance**         | Reduce `max_depth`, increase batch size  |

**[Full Troubleshooting Guide →](./docs/troubleshooting.md)**

### Getting Detailed Help

If troubleshooting doesn't work, gather this information:

```bash
# System info
python --version
python -c "import sys; print(sys.platform)"

# Project info
cd Desktop-AI
git log -1 --oneline

# Ollama status
ollama list

# Error logs
tail -50 logs/desktop_ai.log

# Pip packages
pip freeze > requirements_dump.txt
```

Then share this info with the team.

---

## ❓ FAQ

### Installation & Setup

<details>
<summary><b>Q: Can I use Desktop-AI on Linux/macOS?</b></summary>

**A:** Ollama and Python work on all platforms. The core library is platform-agnostic. The GUI currently targets Windows; Linux/macOS support is in development. You can use all core features via CLI on any platform.

</details>

<details>
<summary><b>Q: Do I need GPU acceleration?</b></summary>

**A:** No, but it's recommended for faster inference. CPU-only works fine but will be slower. See [Configuration Guide](./docs/configuration.md#gpu-acceleration) for GPU setup.

</details>

<details>
<summary><b>Q: How much disk space do I need?</b></summary>

**A:** Desktop-AI itself: ~100MB. Ollama models: 2-13GB depending on the model. For scanning your files, you need space for the SQLite database (typically <1GB per million files).

</details>

### Usage & Features

<details>
<summary><b>Q: Does Desktop-AI modify my files?</b></summary>

**A:** Only if you explicitly use the organizer feature. It always shows a preview first, and you can undo any changes. Your files are never modified without your approval.

</details>

<details>
<summary><b>Q: Can I use different AI models?</b></summary>

**A:** Yes! Any model available via Ollama: Mistral, Llama 2, Zephyr, Neural Chat, etc. See [Ollama models](https://ollama.ai) for the full list. Change the model in your config:

```json
{
  "ai": {
    "model": "llama2"
  }
}
```

</details>

<details>
<summary><b>Q: Is my data private?</b></summary>

**A:** Completely! Everything runs locally on your machine. No data is sent to the cloud. No telemetry or tracking. You have full control.

</details>

### Performance

<details>
<summary><b>Q: Why is scanning slow?</b></summary>

**A:** A few reasons:

- Large directory trees take time to traverse
- HDD (mechanical drives) are slower than SSD
- High `max_depth` setting causes deep recursion

Solutions:

- Reduce `max_depth` in config
- Scan specific folders instead of entire drive
- Use SSD for better performance
- Increase `batch_size` to process more files at once

</details>

<details>
<summary><b>Q: How can I speed up AI classification?</b></summary>

**A:**

- Use faster models: `neural-chat` or `zephyr` instead of `mistral`
- Enable GPU acceleration
- Reduce text extraction for large documents
- Run Ollama on same machine as Desktop-AI

</details>

### Troubleshooting

<details>
<summary><b>Q: Files are not organizing correctly</b></summary>

**A:** Check:

1. Is Ollama running and accessible?
2. Is the model correct? (`ollama list`)
3. Check logs for classification errors
4. Try with a simpler model first
5. Verify folder structure assumptions

See [Troubleshooting Guide](./docs/troubleshooting.md#organization-issues) for detailed steps.

</details>

<details>
<summary><b>Q: Database errors: "database is locked"</b></summary>

**A:** This usually means:

1. Multiple instances running simultaneously
2. Antivirus blocking database access
3. File system issues

Solutions:

- Close other Desktop-AI windows
- Add database file to antivirus whitelist
- Move database to different drive if possible

</details>

### Contributing & Development

<details>
<summary><b>Q: How can I contribute?</b></summary>

**A:** See [Contributing Guide](./CONTRIBUTING.md). We welcome:

- Bug reports and fixes
- Feature implementations
- Documentation improvements
- Test additions

</details>

<details>
<summary><b>Q: Can I use Desktop-AI as a library?</b></summary>

**A:** Yes! All core modules are importable:

```python
from src.scanner import FileScanner
from src.ai import Classifier
from src.search import SemanticSearch

# Use in your own project
```

See [API Reference](./docs/api-reference.md) for documentation.

</details>

---

## 🐛 Reporting Issues

### Before You Report

1. ✅ Check [FAQ](./docs/faq.md) and [Troubleshooting](./docs/troubleshooting.md)
2. ✅ Search [existing issues](https://github.com/gokul-prof-ai/Desktop-AI/issues)
3. ✅ Verify you're using latest version: `git pull`
4. ✅ Try clearing cache/database if relevant

### How to Report a Bug

**Great bug reports include:**

1. **Clear title** — "File scanner crashes with special characters in path"
2. **Detailed description** — What happened, what should happen
3. **Steps to reproduce** — Exact steps to trigger the bug
4. **Expected behavior** — What should happen
5. **Actual behavior** — What actually happened
6. **Environment** — OS, Python version, model, Desktop-AI version
7. **Error output** — Full error message and stack trace
8. **Attachments** — Log file, screenshots, minimal reproducible code

**Example bug report:**

```markdown
**Title:** Scanner crashes with emoji in folder name

**Description:**
When scanning a folder containing emoji characters in the name,
the application crashes with a UnicodeDecodeError.

**Steps to Reproduce:**

1. Create folder: `/Documents/📁Test Folder`
2. Add some files to the folder
3. Run: `python -m src.main`
4. Select the folder and click "Scan"

**Expected:**
Folder should scan successfully, emoji handling gracefully

**Actual:**
Application crashes with error (see logs below)

**Environment:**

- OS: Windows 11
- Python: 3.13.0
- Desktop-AI: latest (commit abc123)
- Ollama: mistral model

**Error Logs:**
```

UnicodeDecodeError: 'utf-8' codec can't decode byte 0xe2 in position 8
File "src/scanner/scanner.py", line 45, in scan
...

```

```

---

## 💡 Feature Requests

### Before You Request

1. ✅ Check [Roadmap](./docs/roadmap.md) — Maybe it's planned!
2. ✅ Search [existing issues](https://github.com/gokul-prof-ai/Desktop-AI/issues) — Maybe someone suggested it
3. ✅ Think about implementation — Is it practical?
4. ✅ Consider impact — Will it benefit many users?

### How to Request a Feature

**Good feature requests include:**

1. **Clear title** — "Add automatic backup feature"
2. **Use case** — Why do you need this?
3. **Expected behavior** — How should it work?
4. **Examples** — Real-world scenarios
5. **Alternatives** — Other solutions you considered
6. **Impact** — Who would benefit?

**Example feature request:**

```markdown
**Title:** Add backup feature before file organization

**Use Case:**
I'm nervous about moving files automatically. It would be great
to have a backup created before any file operations.

**Expected Behavior:**

- When user clicks "Organize", create zip backup first
- Show backup location to user
- Allow rollback by restoring from backup
- Option to auto-clean old backups

**Examples:**

- Professional users dealing with important files
- First-time users learning the feature
- Automated organization mode for advanced users

**Alternatives:**

- Version control integration
- Manual export to safe location
- Time-machine style snapshots

**Implementation:**
Probably could add this in the organizer module,
maybe 100-200 lines of code?
```

---

## 📧 Contact

### Direct Communication

- **Email:** gokul3krish2@gmail.com
- **GitHub Profile:** [@gokul-prof-ai](https://github.com/gokul-prof-ai)

### Expected Response Times

| Channel                  | Response Time |
| ------------------------ | ------------- |
| GitHub Issues (bugs)     | 24-48 hours   |
| GitHub Issues (features) | 48-72 hours   |
| GitHub Discussions       | 24-72 hours   |
| Email                    | 48-72 hours   |
| Security reports         | 24 hours      |

### Support Levels

- **Community Support:** GitHub Issues, Discussions (community + maintainers)
- **Maintainer Support:** Email for critical issues
- **Commercial Support:** Not currently available

---

## 🤝 Getting Help from Community

**GitHub Discussions** is great for peer-to-peer help:

1. Post your question clearly
2. Include relevant context and code
3. Be patient — volunteers answer when they can
4. If someone helps, mark their answer as helpful
5. If you solve it yourself, post the solution to help others

---

## 🎓 Learning Resources

### Documentation

- 📖 [README](./README.md) — Project overview
- 🚀 [Getting Started](./docs/getting-started.md) — Setup guide
- 👤 [User Guide](./docs/user-guide.md) — Feature walkthrough
- 🏗️ [Architecture](./docs/architecture.md) — System design
- 🔧 [Configuration](./docs/configuration.md) — Settings guide
- 📚 [API Reference](./docs/api-reference.md) — Code documentation

### External Resources

- [Ollama Documentation](https://ollama.ai) — LLM setup
- [FAISS Guide](https://faiss.ai) — Semantic search
- [SQLite Docs](https://sqlite.org) — Database
- [PySide6 Guide](https://wiki.qt.io/Qt_for_Python) — GUI

---

<div align="center">

**Have a question? Open an issue or start a discussion!**

[GitHub Issues](https://github.com/gokul-prof-ai/Desktop-AI/issues) •
[GitHub Discussions](https://github.com/gokul-prof-ai/Desktop-AI/discussions) •
[Email](mailto:gokul3krish2@gmail.com)

[Back to README ↑](./README.md)

</div>
