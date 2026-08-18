from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from research_os_v3.status_service import StatusService
from research_os_v3.work_tracker import WorkState, WorkTracker


class StatusRecoveryE2ETests(unittest.TestCase):
    def test_stale_running_work_is_requeued_and_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tracker = WorkTracker(Path(tmp) / "state.json")
            tracker.register("agent-01", "research")
            tracker.transition("agent-01", WorkState.RUNNING.value)
            item = tracker.get("agent-01")
            assert item is not None
            old = datetime.now(timezone.utc) - timedelta(minutes=10)
            tracker.set_last_seen("agent-01", old)

            stale = tracker.stale_items(now=datetime.now(timezone.utc))
            self.assertEqual([x.id for x in stale], ["agent-01"])

            tracker.recover_stale(now=datetime.now(timezone.utc))
            recovered = tracker.get("agent-01")
            assert recovered is not None
            self.assertEqual(recovered.state, WorkState.QUEUED)

            snapshot = StatusService(tracker).snapshot()
            self.assertEqual(snapshot["counts"]["queued"], 1)
            self.assertEqual(snapshot["stale"], [])


if __name__ == "__main__":
    unittest.main()
