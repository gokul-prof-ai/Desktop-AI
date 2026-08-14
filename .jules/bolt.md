## 2024-05-18 - SQLite Individual Insert Bottleneck
**Learning:** SQLite single-row inserts within a loop lead to huge transaction overhead per file. Benchmarking 1000 inserts dropped from 1.65s to 0.04s using batch insertion.
**Action:** When inserting many records into SQLite at once, always use `executemany` with batching instead of a loop calling `execute` to significantly reduce latency.
