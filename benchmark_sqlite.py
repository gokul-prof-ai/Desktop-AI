import sqlite3
import time
from pathlib import Path
from datetime import datetime
from src.scanner.file_info import FileInfo
from src.database.database import DatabaseManager

db_path = Path("test_db.sqlite")
if db_path.exists():
    db_path.unlink()

db = DatabaseManager(db_path)
db.connect()

files = [
    FileInfo(
        name=f"file_{i}.txt",
        path=Path(f"/tmp/file_{i}.txt"),
        extension=".txt",
        size=100,
        created=datetime.now(),
        modified=datetime.now(),
        file_hash="hash",
        detected_type="text/plain"
    )
    for i in range(1000)
]

start = time.time()
for f in files:
    db.save_file(f)
print(f"Individual saves: {time.time() - start:.2f}s")

db.close()
if db_path.exists():
    db_path.unlink()
