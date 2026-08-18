from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from .evidence import Evidence


class SQLiteEvidenceStore:
    """Durable EvidenceStore adapter with deterministic upsert semantics."""

    def __init__(self, path: Path | str) -> None:
        self.path = str(path)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.row_factory = sqlite3.Row
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS evidence (
                id TEXT PRIMARY KEY,
                claim TEXT NOT NULL,
                source_uri TEXT NOT NULL,
                excerpt TEXT NOT NULL,
                task_id TEXT,
                artifact_id TEXT,
                confidence REAL NOT NULL,
                metadata TEXT NOT NULL,
                captured_at TEXT NOT NULL
            )"""
        )
        self._db.commit()

    def add(self, evidence: Evidence) -> Evidence:
        self._db.execute(
            """INSERT INTO evidence
            (id,claim,source_uri,excerpt,task_id,artifact_id,confidence,metadata,captured_at)
            VALUES (?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
              claim=excluded.claim,
              source_uri=excluded.source_uri,
              excerpt=excluded.excerpt,
              task_id=excluded.task_id,
              artifact_id=excluded.artifact_id,
              confidence=excluded.confidence,
              metadata=excluded.metadata,
              captured_at=excluded.captured_at""",
            (evidence.id, evidence.claim, evidence.source_uri, evidence.excerpt,
             evidence.task_id, evidence.artifact_id, evidence.confidence,
             json.dumps(evidence.metadata, sort_keys=True), evidence.captured_at),
        )
        self._db.commit()
        return evidence

    def add_many(self, evidence: Iterable[Evidence]) -> None:
        for item in evidence:
            self.add(item)

    def get(self, evidence_id: str) -> Evidence | None:
        row = self._db.execute("SELECT * FROM evidence WHERE id=?", (evidence_id,)).fetchone()
        return self._from_row(row) if row else None

    def for_task(self, task_id: str) -> tuple[Evidence, ...]:
        rows = self._db.execute(
            "SELECT * FROM evidence WHERE task_id=? ORDER BY captured_at,id", (task_id,)
        ).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def all(self) -> tuple[Evidence, ...]:
        rows = self._db.execute("SELECT * FROM evidence ORDER BY captured_at,id").fetchall()
        return tuple(self._from_row(row) for row in rows)

    def close(self) -> None:
        self._db.close()

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Evidence:
        return Evidence(
            id=row["id"], claim=row["claim"], source_uri=row["source_uri"],
            excerpt=row["excerpt"], task_id=row["task_id"], artifact_id=row["artifact_id"],
            confidence=float(row["confidence"]), metadata=json.loads(row["metadata"]),
            captured_at=row["captured_at"],
        )
