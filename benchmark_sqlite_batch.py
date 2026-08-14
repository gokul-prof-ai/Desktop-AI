import sqlite3
import time
from pathlib import Path
from datetime import datetime
from src.scanner.file_info import FileInfo
from src.database.database import DatabaseManager

class BatchDatabaseManager(DatabaseManager):
    def save_files(self, file_infos: list[FileInfo]) -> None:
        connection = self._require_connection()
        DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
        data = [
            (
                str(f.path),
                f.name,
                f.extension,
                f.size,
                f.created.strftime(DATE_FORMAT),
                f.modified.strftime(DATE_FORMAT),
                f.file_hash,
                f.detected_type,
                datetime.now().strftime(DATE_FORMAT),
            )
            for f in file_infos
        ]
        
        connection.executemany(
            """
            INSERT INTO files
                (path, name, extension, size, created, modified,
                 file_hash, detected_type, scanned_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                name = excluded.name,
                extension = excluded.extension,
                size = excluded.size,
                created = excluded.created,
                modified = excluded.modified,
                file_hash = excluded.file_hash,
                detected_type = excluded.detected_type,
                scanned_at = excluded.scanned_at
            """,
            data,
        )
        connection.commit()

db_path = Path("test_db_batch.sqlite")
if db_path.exists():
    db_path.unlink()

db = BatchDatabaseManager(db_path)
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
db.save_files(files)
print(f"Batch saves: {time.time() - start:.2f}s")

db.close()
if db_path.exists():
    db_path.unlink()
