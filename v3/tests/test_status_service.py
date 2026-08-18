from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_os_v3.status_service import StatusService
from research_os_v3.work_tracker import WorkTracker


class StatusServiceTests(unittest.TestCase):
    def test_snapshot_reports_counts_and_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tracker = WorkTracker(Path(tmp) / "state.json")
            tracker.register("agent-01", "research")
            tracker.register("agent-02", "research")
            tracker.transition("agent-01", "running")
            snapshot = StatusService(tracker).snapshot()

        self.assertEqual(snapshot["total"], 2)
        self.assertEqual(snapshot["counts"]["running"], 1)
        self.assertEqual(snapshot["counts"]["queued"], 1)
        self.assertEqual(len(snapshot["items"]), 2)


if __name__ == "__main__":
    unittest.main()
