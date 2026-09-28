from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from .resource_lineage import ResourceConflictError, ResourceVersionStore, release_and_reconcile_on_conflict


class ResourceLineageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ResourceVersionStore(Path(self.tmp.name) / "lineage.db")
        self.initial = self.store.initialize("A", {"token": 10})

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_matching_version_and_sha_updates(self) -> None:
        updated = self.store.update("A", expected_version=1,
                                    expected_sha256=self.initial.content_sha256,
                                    content={"token": 9})
        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.parent_version, 1)

    def test_stale_update_is_rejected_without_overwrite(self) -> None:
        current = self.store.update("A", expected_version=1,
                                    expected_sha256=self.initial.content_sha256,
                                    content={"token": 9})
        with self.assertRaises(ResourceConflictError) as caught:
            self.store.update("A", expected_version=1,
                              expected_sha256=self.initial.content_sha256,
                              content={"token": 8})
        self.assertEqual(caught.exception.evidence.execution_disposition, "stop")
        self.assertEqual(caught.exception.evidence.resource_disposition, "release")
        self.assertEqual(self.store.head("A").content_sha256, current.content_sha256)
        self.assertEqual(len(self.store.list_conflicts("A")), 1)

    def test_stale_sha_is_rejected(self) -> None:
        with self.assertRaises(ResourceConflictError):
            self.store.update("A", expected_version=1, expected_sha256="wrong",
                              content={"token": 8})
        self.assertEqual(self.store.head("A").version, 1)

    def test_historical_version_can_branch_without_replacing_head(self) -> None:
        current = self.store.update("A", expected_version=1,
                                    expected_sha256=self.initial.content_sha256,
                                    content={"token": 9})
        alternate = self.store.branch("A", parent_version=1, content={"token": 7})
        self.assertEqual(alternate.parent_version, 1)
        self.assertEqual(self.store.head("A").version, current.version)
        self.assertEqual(self.store.head("A").content_sha256, current.content_sha256)

    def test_conflict_releases_and_reconciles(self) -> None:
        events: list[str] = []
        with self.assertRaises(ResourceConflictError) as caught:
            self.store.update("A", expected_version=1, expected_sha256="wrong",
                              content={"token": 8})
        release_and_reconcile_on_conflict(
            caught.exception.evidence,
            release_resources=lambda: events.append("release"),
            reconcile_delivery=lambda e: events.append("reconcile:" + e.action),
        )
        self.assertEqual(events, ["release", "reconcile:UPDATE_REJECTED"])


if __name__ == "__main__":
    unittest.main()
