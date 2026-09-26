import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools import platform_work_checkpoint as checkpoint


class PlatformWorkCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.previous = os.environ.get("RESEARCH_OS_DATA_DIR")
        os.environ["RESEARCH_OS_DATA_DIR"] = self.tmp.name
        self.sha = "a" * 40

    def tearDown(self):
        if self.previous is None:
            os.environ.pop("RESEARCH_OS_DATA_DIR", None)
        else:
            os.environ["RESEARCH_OS_DATA_DIR"] = self.previous
        self.tmp.cleanup()

    def test_round_trip_is_compact_and_persistent(self):
        with patch.object(checkpoint, "canonical_sha", return_value=self.sha):
            record = checkpoint.create_checkpoint(
                owner_id="owner",
                task_id="task-1",
                workflow_state="PAUSED",
                current_step="final-gate",
                completed_steps=["recon"],
                pending_steps=["verify"],
                evidence_refs=["current/PLATFORM_OPERATIONALIZATION_CONTRACT.json"],
                deferred_work=["flutter"],
                context_refs=["current/RESEARCH_OS_CONTEXT_RECOVERY.json"],
                next_action="verify",
            )
            records = checkpoint.list_checkpoints("owner", "task-1")
            self.assertEqual(record["checkpoint_id"], records[0]["checkpoint_id"])
            self.assertEqual(record["source_sha"], self.sha)
            self.assertNotIn("messages", record)
            self.assertNotIn("reasoning", record)

    def test_resume_is_ready_when_source_matches(self):
        with patch.object(checkpoint, "canonical_sha", return_value=self.sha):
            record = checkpoint.create_checkpoint(
                owner_id="owner",
                task_id="task-2",
                workflow_state="ACTIVE",
                current_step="implementation",
            )
            result = checkpoint.resume_checkpoint("owner", record["checkpoint_id"])
            self.assertEqual("READY", result["status"])
            self.assertEqual("implementation" if result["next_action"] == "implementation" else "recon", result["next_action"])

    def test_resume_holds_on_sha_drift(self):
        with patch.object(checkpoint, "canonical_sha", side_effect=[self.sha, "b" * 40]):
            record = checkpoint.create_checkpoint(
                owner_id="owner",
                task_id="task-3",
                workflow_state="PAUSED",
                current_step="verify",
            )
            result = checkpoint.resume_checkpoint("owner", record["checkpoint_id"])
            self.assertEqual("HOLD", result["status"])
            self.assertIn("source_sha_mismatch", result["failures"])

    def test_owner_and_path_safe_ids(self):
        with patch.object(checkpoint, "canonical_sha", return_value=self.sha):
            with self.assertRaises(ValueError):
                checkpoint.create_checkpoint(
                    owner_id="../owner",
                    task_id="task",
                    workflow_state="ACTIVE",
                    current_step="x",
                )
            with self.assertRaises(ValueError):
                checkpoint.create_checkpoint(
                    owner_id="owner",
                    task_id="task",
                    workflow_state="ACTIVE",
                    current_step="x",
                    context_refs=["x" * 513],
                )


if __name__ == "__main__":
    unittest.main()
