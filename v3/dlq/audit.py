from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock


@dataclass(frozen=True)
class ReplayAuditEvent:
    task_id: str
    actor: str
    action: str
    authorized: bool
    timestamp: datetime
    reason: str | None = None


class ReplayAuthorizer:
    """Explicit authorization boundary for DLQ replay operations."""

    def __init__(self, allowed_actors: set[str] | None = None) -> None:
        self._allowed = allowed_actors or set()

    def authorize(self, actor: str) -> bool:
        return bool(actor) and actor in self._allowed


class ReplayAuditLog:
    """In-process audit sink; durable sinks can implement the same contract."""

    def __init__(self) -> None:
        self._events: list[ReplayAuditEvent] = []
        self._lock = RLock()

    def record(self, task_id: str, actor: str, action: str, authorized: bool, reason: str | None = None) -> None:
        event = ReplayAuditEvent(
            task_id=task_id,
            actor=actor,
            action=action,
            authorized=authorized,
            timestamp=datetime.now(timezone.utc),
            reason=reason,
        )
        with self._lock:
            self._events.append(event)

    def events(self) -> list[ReplayAuditEvent]:
        with self._lock:
            return list(self._events)
