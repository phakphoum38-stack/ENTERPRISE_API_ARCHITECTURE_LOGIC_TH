from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class WorkState(str, Enum):
    BACKLOG = "backlog"
    READY = "ready"
    QUEUED = "queued"  # backward-compatible alias/state
    RUNNING = "running"
    BLOCKED = "blocked"
    VERIFY = "verify"
    PAUSED = "paused"  # backward-compatible state
    FAILED = "failed"  # backward-compatible state
    DONE = "done"
    COMPLETED = "completed"  # backward-compatible alias/state
    LOCKED = "locked"


@dataclass
class WorkItem:
    work_id: str
    agent_id: str
    state: WorkState = WorkState.QUEUED
    owner_id: str | None = None
    assistant_ids: list[str] = field(default_factory=list)
    issue_url: str | None = None
    pr_url: str | None = None
    commit_sha: str | None = None
    actions_run_url: str | None = None
    dependencies: list[str] = field(default_factory=list)
    blocker: str | None = None
    next_action: str | None = None
    ci_status: str | None = None
    evidence: list[str] = field(default_factory=list)
    handoff: str | None = None
    started_at: float | None = None
    last_seen: float | None = None
    attempts: int = 0
    error: str | None = None


class PersistentWorkTracker:
    """Existing JSON-backed tracker extended into the canonical evidence control plane.

    GitHub remains the source of truth; this component stores references and
    verification state rather than inventing repository status.
    """

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
        if not isinstance(raw, dict):
            return
        loaded: dict[str, WorkItem] = {}
        for item in raw.get("items", []):
            if not isinstance(item, dict) or "work_id" not in item or "agent_id" not in item:
                continue
            data = dict(item)
            data["state"] = WorkState(data.get("state", WorkState.QUEUED.value))
            data.setdefault("assistant_ids", [])
            data.setdefault("dependencies", [])
            data.setdefault("evidence", [])
            loaded[data["work_id"]] = WorkItem(**data)
        self._items = loaded

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {"schema_version": 2, "items": [asdict(item) for item in self._items.values()]},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)

    def register(
        self,
        work_id: str,
        agent_id: str,
        *,
        owner_id: str | None = None,
        assistant_ids: Iterable[str] = (),
        issue_url: str | None = None,
        dependencies: Iterable[str] = (),
        next_action: str | None = None,
    ) -> WorkItem:
        with self._lock:
            item = self._items.get(work_id)
            if item is None:
                item = WorkItem(
                    work_id=work_id,
                    agent_id=agent_id,
                    owner_id=owner_id,
                    assistant_ids=list(assistant_ids),
                    issue_url=issue_url,
                    dependencies=list(dependencies),
                    next_action=next_action,
                )
                self._items[work_id] = item
                self._save()
            return item

    def transition(self, work_id: str, state: WorkState, error: str | None = None) -> WorkItem:
        with self._lock:
            item = self._items[work_id]
            now = self.clock()
            item.state = WorkState(state)
            item.last_seen = now
            item.error = error
            if state is WorkState.RUNNING:
                item.started_at = item.started_at or now
                item.attempts += 1
            self._save()
            return item

    def update_metadata(self, work_id: str, **changes: object) -> WorkItem:
        allowed = {
            "owner_id", "assistant_ids", "issue_url", "pr_url", "commit_sha",
            "actions_run_url", "dependencies", "blocker", "next_action",
            "ci_status", "evidence", "handoff",
        }
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"unknown work metadata: {sorted(unknown)}")
        with self._lock:
            item = self._items[work_id]
            for key, value in changes.items():
                if key in {"assistant_ids", "dependencies", "evidence"} and value is not None:
                    value = list(value)  # type: ignore[arg-type]
                setattr(item, key, value)
            item.last_seen = self.clock()
            self._save()
            return item

    def add_evidence(self, work_id: str, reference: str) -> WorkItem:
        reference = reference.strip()
        if not reference:
            raise ValueError("evidence reference cannot be empty")
        with self._lock:
            item = self._items[work_id]
            if reference not in item.evidence:
                item.evidence.append(reference)
            item.last_seen = self.clock()
            self._save()
            return item

    def can_handoff(self, work_id: str) -> bool:
        with self._lock:
            item = self._items[work_id]
            return bool(
                item.owner_id
                and item.issue_url
                and item.evidence
                and item.ci_status == "passed"
                and not item.blocker
            )

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
                item
                for item in self._items.values()
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
                item.last_seen = self.clock() if now is None else now
            if stale:
                self._save()
        return stale

    def summary(self) -> dict[str, int]:
        with self._lock:
            return {
                state.value: sum(item.state is state for item in self._items.values())
                for state in WorkState
            }

    def items(self) -> Iterable[WorkItem]:
        with self._lock:
            return list(self._items.values())


# Backward-compatible public API used by v3 consumers and tests.
WorkTracker = PersistentWorkTracker
