from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_os_v3.status_service import StatusService
from research_os_v3.work_tracker import PersistentWorkTracker, WorkState


class StatusRecoveryE2ETests(unittest.TestCase):
    def test_stale_running_work_is_requeued_and_visible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            now = [1_000.0]
            tracker = PersistentWorkTracker(Path(tmp) / "state.json", clock=lambda: now[0])
            tracker.register("work-01", "agent-01")
            tracker.transition("work-01", WorkState.RUNNING)

            now[0] = 1_601.0
            stale = tracker.stale(timeout_seconds=600.0)
            self.assertEqual([item.work_id for item in stale], ["work-01"])

            recovered = tracker.recover_stale(timeout_seconds=600.0)
            self.assertEqual([item.work_id for item in recovered], ["work-01"])
            item = list(tracker.items())[0]
            self.assertEqual(item.state, WorkState.QUEUED)
            self.assertEqual(item.error, "stale-heartbeat-recovered")

            snapshot = StatusService(tracker).snapshot(stale_timeout_seconds=600.0)
            self.assertEqual(snapshot["counts"]["queued"], 1)
            self.assertEqual(snapshot["stale"], [])


if __name__ == "__main__":
    unittest.main()
