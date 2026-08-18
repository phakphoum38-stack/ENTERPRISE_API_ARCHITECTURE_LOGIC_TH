from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .work_tracker import WorkState, WorkTracker


class StatusService:
    """Read-only operational view over the persistent work tracker."""

    def __init__(self, tracker: WorkTracker) -> None:
        self.tracker = tracker

    def snapshot(self) -> dict[str, Any]:
        items = list(self.tracker.items())
        counts = {state.value: 0 for state in WorkState}
        stale: list[str] = []
        now = datetime.now(timezone.utc)
        for item in items:
            counts[item.state.value] += 1
            if self.tracker.is_stale(item, now=now):
                stale.append(item.id)
        return {
            "generated_at": now.isoformat(),
            "total": len(items),
            "counts": counts,
            "stale": stale,
            "items": [asdict(item) for item in items],
        }
