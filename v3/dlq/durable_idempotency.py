from __future__ import annotations

import sqlite3
from threading import RLock


class SQLiteIdempotencyRegistry:
    """Durable idempotency registry for replay delivery keys.

    The database transaction makes claim atomic across process restarts. A
    release is explicit and is used when queue delivery did not complete.
    """

    def __init__(self, database: str = ":memory:") -> None:
        self._db = sqlite3.connect(database, check_same_thread=False)
        self._lock = RLock()
        with self._db:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS replay_keys (key TEXT PRIMARY KEY)"
            )

    def claim(self, key: str) -> bool:
        if not key:
            raise ValueError("idempotency key is required")
        with self._lock, self._db:
            cursor = self._db.execute(
                "INSERT OR IGNORE INTO replay_keys(key) VALUES (?)", (key,)
            )
            return cursor.rowcount == 1

    def release(self, key: str) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM replay_keys WHERE key = ?", (key,))

    def is_claimed(self, key: str) -> bool:
        if not key:
            return False
        with self._lock:
            row = self._db.execute(
                "SELECT 1 FROM replay_keys WHERE key = ?", (key,)
            ).fetchone()
            return row is not None

    def close(self) -> None:
        with self._lock:
            self._db.close()
