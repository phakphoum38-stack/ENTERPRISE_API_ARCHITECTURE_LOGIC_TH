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

    def test_evidence_handoff_requires_owner_ci_and_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tracker = PersistentWorkTracker(Path(tmp) / "tracker.json")
            tracker.register(
                "w3",
                "set-a",
                owner_id="owner-a",
                issue_url="https://github.com/example/repo/issues/130",
            )
            self.assertFalse(tracker.can_handoff("w3"))
            tracker.update_metadata("w3", ci_status="passed", pr_url="https://github.com/example/repo/pull/1")
            self.assertFalse(tracker.can_handoff("w3"))
            tracker.add_evidence("w3", "actions://run/123")
            self.assertTrue(tracker.can_handoff("w3"))

    def test_dependency_and_owner_metadata_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tracker.json"
            tracker = PersistentWorkTracker(path)
            tracker.register("w4", "set-c", owner_id="owner-c", assistant_ids=["a1", "a2"], dependencies=["w1"], next_action="verify")
            tracker.update_metadata("w4", blocker="waiting-for-w1", ci_status="pending")
            restored = PersistentWorkTracker(path)
            item = next(iter(restored.items()))
            self.assertEqual(item.owner_id, "owner-c")
            self.assertEqual(item.assistant_ids, ["a1", "a2"])
            self.assertEqual(item.dependencies, ["w1"])
            self.assertEqual(item.blocker, "waiting-for-w1")


if __name__ == "__main__":
    unittest.main()
