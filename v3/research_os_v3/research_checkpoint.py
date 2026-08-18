from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3


@dataclass(frozen=True)
class ResearchCheckpoint:
    run_id: str
    plan_question: str
    completed_tasks: tuple[str, ...] = ()
    failed_tasks: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResearchCheckpointStore:
    """Durable checkpoint store for pause/resume of research runs."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(self.path)
        self._db.execute(
            """CREATE TABLE IF NOT EXISTS research_checkpoints (
                run_id TEXT PRIMARY KEY,
                plan_question TEXT NOT NULL,
                completed_tasks TEXT NOT NULL,
                failed_tasks TEXT NOT NULL,
                evidence_ids TEXT NOT NULL,
                metadata TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        self._db.commit()

    def save(self, checkpoint: ResearchCheckpoint) -> ResearchCheckpoint:
        self._db.execute(
            """INSERT INTO research_checkpoints
            (run_id, plan_question, completed_tasks, failed_tasks, evidence_ids, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
              plan_question=excluded.plan_question,
              completed_tasks=excluded.completed_tasks,
              failed_tasks=excluded.failed_tasks,
              evidence_ids=excluded.evidence_ids,
              metadata=excluded.metadata,
              updated_at=excluded.updated_at""",
            (
                checkpoint.run_id,
                checkpoint.plan_question,
                json.dumps(checkpoint.completed_tasks),
                json.dumps(checkpoint.failed_tasks),
                json.dumps(checkpoint.evidence_ids),
                json.dumps(checkpoint.metadata, sort_keys=True),
                checkpoint.updated_at,
            ),
        )
        self._db.commit()
        return checkpoint

    def load(self, run_id: str) -> ResearchCheckpoint | None:
        row = self._db.execute(
            "SELECT run_id, plan_question, completed_tasks, failed_tasks, evidence_ids, metadata, updated_at "
            "FROM research_checkpoints WHERE run_id = ?",
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return ResearchCheckpoint(
            run_id=row[0],
            plan_question=row[1],
            completed_tasks=tuple(json.loads(row[2])),
            failed_tasks=tuple(json.loads(row[3])),
            evidence_ids=tuple(json.loads(row[4])),
            metadata=dict(json.loads(row[5])),
            updated_at=row[6],
        )

    def delete(self, run_id: str) -> None:
        self._db.execute("DELETE FROM research_checkpoints WHERE run_id = ?", (run_id,))
        self._db.commit()

    def close(self) -> None:
        self._db.close()
