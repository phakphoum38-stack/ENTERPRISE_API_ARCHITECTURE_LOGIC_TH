from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class WorkState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    BLOCKED = "blocked"
    PAUSED = "paused"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class WorkItem:
    work_id: str
    agent_id: str
    state: WorkState = WorkState.QUEUED
    started_at: float | None = None
    last_seen: float | None = None
    attempts: int = 0
    error: str | None = None


class PersistentWorkTracker:
    """Small JSON-backed control-plane tracker; safe for process-local concurrent updates."""

    def __init__(self, path: str | Path, clock=time.time) -> None:
        self.path = Path(path)
        self.clock = clock
        self._lock = threading.RLock()
        self._items: dict[str, WorkItem] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self._items = {
            item["work_id"]: WorkItem(
                **{**item, "state": WorkState(item["state"])}
            )
            for item in raw.get("items", [])
        }

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"items": [asdict(item) for item in self._items.values()]}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def register(self, work_id: str, agent_id: str) -> WorkItem:
        with self._lock:
            item = self._items.get(work_id)
            if item is None:
                item = WorkItem(work_id=work_id, agent_id=agent_id)
                self._items[work_id] = item
                self._save()
            return item

    def transition(self, work_id: str, state: WorkState, error: str | None = None) -> WorkItem:
        with self._lock:
            item = self._items[work_id]
            now = self.clock()
            item.state = state
            item.last_seen = now
            item.error = error
            if state is WorkState.RUNNING:
                item.started_at = item.started_at or now
                item.attempts += 1
            self._save()
            return item

    def heartbeat(self, work_id: str) -> WorkItem:
        with self._lock:
            item = self._items[work_id]
            item.last_seen = self.clock()
            self._save()
            return item

    def stale(self, timeout_seconds: float, now: float | None = None) -> list[WorkItem]:
        now = self.clock() if now is None else now
        with self._lock:
            return [
                item for item in self._items.values()
                if item.state is WorkState.RUNNING
                and item.last_seen is not None
                and now - item.last_seen > timeout_seconds
            ]

    def recover_stale(self, timeout_seconds: float, now: float | None = None) -> list[WorkItem]:
        stale = self.stale(timeout_seconds, now)
        with self._lock:
            for item in stale:
                item.state = WorkState.QUEUED
                item.error = "stale-heartbeat-recovered"
            if stale:
                self._save()
        return stale

    def summary(self) -> dict[str, int]:
        with self._lock:
            return {state.value: sum(item.state is state for item in self._items.values()) for state in WorkState}

    def items(self) -> Iterable[WorkItem]:
        with self._lock:
            return list(self._items.values())
