from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_os_v3.work_tracker import PersistentWorkTracker, WorkState


class WorkTrackerTests(unittest.TestCase):
    def test_persists_lifecycle_and_recovers_stale_work(self) -> None:
        now = [100.0]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tracker.json"
            tracker = PersistentWorkTracker(path, clock=lambda: now[0])
            tracker.register("w1", "domain.runtime.runner")
            tracker.transition("w1", WorkState.RUNNING)
            now[0] = 200.0
            stale = tracker.stale(50)
            self.assertEqual([item.work_id for item in stale], ["w1"])
            tracker.recover_stale(50)
            self.assertEqual(tracker.summary()["queued"], 1)

            restored = PersistentWorkTracker(path, clock=lambda: now[0])
            item = next(iter(restored.items()))
            self.assertEqual(item.state, WorkState.QUEUED)
            self.assertEqual(item.error, "stale-heartbeat-recovered")

    def test_heartbeat_prevents_false_stale_detection(self) -> None:
        now = [100.0]
        with tempfile.TemporaryDirectory() as tmp:
            tracker = PersistentWorkTracker(Path(tmp) / "tracker.json", clock=lambda: now[0])
            tracker.register("w2", "domain.tools.web")
            tracker.transition("w2", WorkState.RUNNING)
            now[0] = 140.0
            tracker.heartbeat("w2")
            now[0] = 160.0
            self.assertEqual(tracker.stale(30), [])


if __name__ == "__main__":
    unittest.main()
