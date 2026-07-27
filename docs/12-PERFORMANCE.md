# Performance Guide

## Benchmarks (Baseline)

Machine: Intel i7, 16GB RAM, SSD

- Scanning 10K files: ~50 seconds
- Classification per file: ~500ms
- Semantic search (10K files): ~200ms
- Undo operation: ~100ms

## Optimization Strategies

### 1. Scanning

**Target:** 1,000+ files/sec

**Optimizations:**

- Exclude unnecessary folders
- Reduce `max_depth`
- Use SSD (not HDD)
- Disable antivirus for scan duration

**Config:**

```yaml
scanner:
  max_depth: 3
  ignore_patterns:
    - .git
    - node_modules
    - __pycache__
    - .venv
```

### 2. AI Classification

**Target:** 5-10 files/sec

**Optimizations:**

- Use faster model: `model: tinyllama` (vs mistral)
- Batch processing (10 files at once)
- Disable for small files (< 1KB)

**Config:**

```yaml
ai:
  model: tinyllama
  batch_size: 10
  skip_if_size_kb: 1
```

### 3. Semantic Search

**Target:** 100-200ms for 10K items

**Optimizations:**

- Use HNSW index for large datasets
- Reduce `top_k` if only need few results
- Enable approximate search mode

**Config:**

```yaml
search:
  faiss_index_type: hnsw
  top_k: 5
  use_gpu: true # If CUDA available
```

## Profiling Guide

### Identify Bottlenecks

```bash
python -m cProfile -s cumtime src/app.py <folder>
```

### Memory Profiling

```bash
pip install memory-profiler
python -m memory_profiler src/app.py <folder>
```

## Load Testing

How to test with large datasets:

```bash
# Generate 100K test files
python scripts/generate_test_files.py --count 100000

# Run performance test
pytest tests/test_performance.py -v
```
