import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4


class Store:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version > 1:
                raise RuntimeError("Database is newer than this app; refusing to modify it")
            db.execute("PRAGMA journal_mode=WAL")
            db.execute(
                "CREATE TABLE IF NOT EXISTS runs "
                "(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS feedback "
                "(id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL)"
            )
            db.execute("PRAGMA user_version=1")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def add(self, table: str, payload: dict) -> dict:
        if table not in ("runs", "feedback"):
            raise ValueError("Invalid collection")
        record = {"id": str(uuid4()), "created_at": datetime.now(UTC).isoformat(), **payload}
        with self.connect() as db:
            if db.execute(f"SELECT count(*) FROM {table}").fetchone()[0] >= 10000:
                raise ValueError("Local storage limit reached; export and archive the database")
            db.execute(
                f"INSERT INTO {table} VALUES (?, ?, ?)",
                (record["id"], record["created_at"], json.dumps(record)),
            )
        return record

    def list(self, table: str, limit=100) -> list[dict]:
        if table not in ("runs", "feedback"):
            raise ValueError("Invalid collection")
        with self.connect() as db:
            return [
                json.loads(r[0])
                for r in db.execute(
                    f"SELECT payload FROM {table} ORDER BY created_at DESC LIMIT ?", (limit,)
                )
            ]
