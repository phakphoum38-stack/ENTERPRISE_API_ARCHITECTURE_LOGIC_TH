import tempfile
import unittest
from pathlib import Path

from research_os_friend.learning import LearningRecord, PersistentLearningStore


class PersistentLearningStoreTests(unittest.TestCase):
    def _record(self, owner_id="owner", validation_result="passed"):
        return LearningRecord(
            record_id="lr-001",
            owner_id=owner_id,
            skill_id="repair.flutter.windows",
            trigger="windows build failure",
            decision_source="test",
            tools_used=("github.repository_status",),
            source_commit="abc123",
            source_workflow_run="run-1",
            changed_files=("owner_special/flutter_app",),
            validation_result=validation_result,
            pr_reference="#236",
            verification_timestamp="2026-09-06T00:00:00Z",
            confidence=0.95,
            evidence=("evidence://run-1",),
        )

    def test_round_trip_and_reusable_promotion(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PersistentLearningStore(Path(tmp) / "learning.json")
            store.add(self._record())
            promoted = store.promote("lr-001", "validated")
            self.assertEqual(promoted.state, "validated")
            promoted = store.promote("lr-001", "reusable", evidence=("evidence://run-1",))
            self.assertEqual(promoted.state, "reusable")
            self.assertEqual(promoted.version, 3)
            reloaded = PersistentLearningStore(Path(tmp) / "learning.json")
            self.assertEqual(len(reloaded.reusable(owner_id="owner", skill_id="repair.flutter.windows")), 1)

    def test_failed_validation_cannot_become_reusable(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PersistentLearningStore(Path(tmp) / "learning.json")
            store.add(self._record(validation_result="failed"))
            with self.assertRaises(ValueError):
                store.promote("lr-001", "reusable")

    def test_owner_scope_isolation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PersistentLearningStore(Path(tmp) / "learning.json")
            store.add(self._record(owner_id="owner"))
            store.promote("lr-001", "validated")
            store.promote("lr-001", "reusable")
            self.assertEqual(store.reusable(owner_id="other"), ())

    def test_lifecycle_cannot_skip_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PersistentLearningStore(Path(tmp) / "learning.json")
            store.add(self._record())
            with self.assertRaises(ValueError):
                store.promote("lr-001", "reusable")

    def test_rejected_is_terminal(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = PersistentLearningStore(Path(tmp) / "learning.json")
            store.add(self._record())
            store.promote("lr-001", "rejected")
            with self.assertRaises(ValueError):
                store.promote("lr-001", "validated")

    def test_core_record_is_versioned_and_fingerprinted(self):
        record = self._record()
        self.assertEqual(record.version, 1)
        self.assertEqual(len(record.fingerprint), 64)
        self.assertEqual(record.skill_id, "repair.flutter.windows")


if __name__ == "__main__":
    unittest.main()
