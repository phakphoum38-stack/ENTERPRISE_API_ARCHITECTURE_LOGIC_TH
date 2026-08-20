from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .work_tracker import PersistentWorkTracker


class StatusService:
    """Read-only operational view over the persistent work tracker."""

    def __init__(self, tracker: PersistentWorkTracker) -> None:
        self.tracker = tracker

    def snapshot(self, stale_timeout_seconds: float = 60.0) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        stale = self.tracker.stale(stale_timeout_seconds, now=now.timestamp())
        return {
            "generated_at": now.isoformat(),
            "total": len(list(self.tracker.items())),
            "counts": self.tracker.summary(),
            "stale": [item.work_id for item in stale],
            "items": [
                {
                    "work_id": item.work_id,
                    "agent_id": item.agent_id,
                    "state": item.state.value,
                    "started_at": item.started_at,
                    "last_seen": item.last_seen,
                    "attempts": item.attempts,
                    "error": item.error,
                }
                for item in self.tracker.items()
            ],
        }
