from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from research_os_v3.research_checkpoint import ResearchCheckpoint, ResearchCheckpointStore


class ResearchCheckpointTests(unittest.TestCase):
    def test_checkpoint_survives_store_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "research.sqlite"
            checkpoint = ResearchCheckpoint(
                run_id="run-1",
                plan_question="What is the architecture?",
                completed_tasks=("task-a", "task-b"),
                failed_tasks=(),
                evidence_ids=("e-1",),
                metadata={"status": "paused"},
            )
            first = ResearchCheckpointStore(path)
            first.save(checkpoint)
            first.close()

            second = ResearchCheckpointStore(path)
            restored = second.load("run-1")
            second.close()

            self.assertEqual(restored, checkpoint)

    def test_missing_checkpoint_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ResearchCheckpointStore(Path(tmp) / "research.sqlite")
            self.assertIsNone(store.load("missing"))
            store.close()


if __name__ == "__main__":
    unittest.main()
