from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from owner_special.research_os_friend.runtime import FriendRuntime


class LearningPersistenceRuntimeTests(unittest.TestCase):
    def test_approved_learning_is_persisted_and_reloaded_by_owner_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp)
            previous = os.environ.get("RESEARCH_OS_SOURCE_SHA")
            os.environ["RESEARCH_OS_SOURCE_SHA"] = "test-source-sha"
            try:
                runtime = FriendRuntime.create_owner_special("owner", data_root=data_root)
                approved = runtime.learn_skill(
                    name="learned-persistent-review",
                    goal="Repeat a verified repository review",
                    procedure=("inspect", "validate", "record evidence"),
                    evidence=("test-pass", "review-pass"),
                    confidence=0.95,
                )
                self.assertIsNotNone(approved)
                self.assertEqual(runtime.learning_store.count(), 1)
                self.assertEqual(len(runtime.learning_store.reusable(owner_id="owner")), 1)
                self.assertEqual(runtime.self_learning_snapshot()["persistent_reusable"], 1)

                reloaded = FriendRuntime.create_owner_special("owner", data_root=data_root)
                self.assertEqual(reloaded.learning_store.count(), 1)
                self.assertEqual(len(reloaded.learning_store.reusable(owner_id="owner")), 1)
                self.assertEqual(reloaded.self_learning_snapshot()["source_commit"], "test-source-sha")
            finally:
                if previous is None:
                    os.environ.pop("RESEARCH_OS_SOURCE_SHA", None)
                else:
                    os.environ["RESEARCH_OS_SOURCE_SHA"] = previous

    def test_non_persistent_runtime_keeps_existing_in_memory_behavior(self):
        runtime = FriendRuntime.create_owner_special("owner")
        self.assertIsNone(runtime.learning_store)
        snapshot = runtime.self_learning_snapshot()
        self.assertEqual(snapshot["persistence"], "disabled")
        self.assertEqual(snapshot["persistent_records"], 0)


if __name__ == "__main__":
    unittest.main()
