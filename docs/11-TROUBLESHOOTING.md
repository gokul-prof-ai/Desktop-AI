# Troubleshooting Guide

## Installation Issues

### Q: "ModuleNotFoundError: No module named 'src'"

**A:** Run from repository root: `cd Desktop-AI && python src/app.py`

### Q: "Ollama connection refused"

**A:**

1. Verify Ollama running: `ollama list`
2. Check config: `config/config.yaml` (should have `host: localhost:11434`)
3. Restart Ollama: `ollama serve`

### Q: "Tesseract not found"

**A:** Install tesseract-ocr on Windows:

```bash
winget install UB-Techsoft.Tesseract-OCR
# Or download: https://github.com/UB-Techsoft/Tesseract-OCR
```

## Runtime Issues

### Q: "Database locked" error

**A:**

- Close other instances of DesktopAI
- Delete `data/desktop_ai.db.lock` if stuck
- Restart the application

### Q: "Scan is very slow (< 100 files/sec)"

**A:**

- Check CPU/disk usage
- Reduce `max_depth` in config
- Exclude more folders with `ignore_patterns`
- Check disk for bad sectors

### Q: "Search returns irrelevant results"

**A:**

- Query must be natural language: "Find PDFs about budgets"
- Results improve after 100+ scanned documents
- Try rephrasing query
- Check `similarity_threshold` in config

## Performance Issues

### High Memory Usage

**Solutions:**

- Reduce `cache_ttl_seconds`
- Limit batch size in organizer
- Use `file_size_limit_mb`

### Slow Semantic Search

**Causes & Fixes:**

- First search builds FAISS index (wait 30 sec)
- Large dataset needs HNSW index: change `faiss_index_type: hnsw`
- Check disk speed with `crystaldiskinfo`

## FAQ

**Q: Can I use this on Linux/Mac?**
A: Scanner works, but GUI/Watcher Windows-only (v1.0). WSL2 is supported.

**Q: Does this upload data to cloud?**
A: No, 100% offline. All processing local.

**Q: Can I use GPU for search?**
A: Yes, FAISS supports GPU. Use `gpu_index_type` in config (requires CUDA).

**Q: How much disk space needed?**
A: ~500MB for app + index. Database grows ~10MB per 10K files.
