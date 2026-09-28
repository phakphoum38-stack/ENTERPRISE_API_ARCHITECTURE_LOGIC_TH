from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from .durable_events import WorkflowEvent


_EVENT_STATES = {
    "task.queued": "QUEUED",
    "task.started": "RUNNING",
    "task.retry_scheduled": "RETRY_WAIT",
    "task.requeued": "QUEUED",
    "task.succeeded": "SUCCEEDED",
    "task.completed": "SUCCEEDED",
    "task.failed": "FAILED",
    "task.timed_out": "TIMED_OUT",
    "task.cancelled": "CANCELLED",
}
_TERMINAL = {"SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELLED"}


@dataclass(frozen=True)
class ProjectedTask:
    workflow_id: str
    task_id: str
    state: str
    sequence: int
    last_event_id: str


class WorkflowStateProjector:
    """Idempotent workflow-engine state projection from durable events."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS workflow_task_state (
                    workflow_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    state TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    last_event_id TEXT NOT NULL,
                    PRIMARY KEY(workflow_id, task_id)
                )"""
            )
            db.execute(
                """CREATE TABLE IF NOT EXISTS projected_events (
                    event_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL
                )"""
            )

    def apply(self, event: WorkflowEvent) -> bool:
        state = _EVENT_STATES.get(event.event_type)
        if state is None:
            return False
        with sqlite3.connect(self.path) as db:
            if db.execute(
                "SELECT 1 FROM projected_events WHERE event_id=?", (event.event_id,)
            ).fetchone():
                return False
            current = db.execute(
                "SELECT state, sequence FROM workflow_task_state WHERE workflow_id=? AND task_id=?",
                (event.workflow_id, event.task_id),
            ).fetchone()
            if current is not None:
                current_state, current_sequence = current
                if event.sequence <= current_sequence:
                    return False
                if current_state in _TERMINAL:
                    raise ValueError("terminal workflow task cannot transition")
            db.execute(
                "INSERT OR REPLACE INTO workflow_task_state VALUES (?, ?, ?, ?, ?)",
                (event.workflow_id, event.task_id, state, event.sequence, event.event_id),
            )
            db.execute(
                "INSERT INTO projected_events VALUES (?, ?, ?, ?)",
                (event.event_id, event.workflow_id, event.task_id, event.sequence),
            )
        return True

    def get(self, workflow_id: str, task_id: str) -> ProjectedTask | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute(
                "SELECT workflow_id,task_id,state,sequence,last_event_id FROM workflow_task_state WHERE workflow_id=? AND task_id=?",
                (workflow_id, task_id),
            ).fetchone()
        return ProjectedTask(*row) if row else None
