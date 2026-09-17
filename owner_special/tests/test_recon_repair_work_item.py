"""Regression tests for the P0-4 RECON → AEOS WorkItem bridge."""
from __future__ import annotations
import json
import unittest
from types import SimpleNamespace

from owner_special.research_os_friend.canonical_identity_federation import CanonicalIdentity
from owner_special.research_os_friend.recon_failure import FailureKind, ingest_failure
from owner_special.research_os_friend.recon_repair_work_item import (
    ReconRepairMappingError, build_repair_work_item,
)

SHA="a"*40

def repair_set():
    return SimpleNamespace(
        root_causes=("missing_contract",),
        intents=("restore_contract_validation",),
        changed_files=("tools/example.py",),
        regression_tests=("tests/test_example.py",),
        fingerprint="b"*64,
    )

class ReconRepairWorkItemTests(unittest.TestCase):
    def setUp(self):
        self.failure=ingest_failure(
            source_sha=SHA, gate="gate-x", test="test-x",
            error_class="AssertionError", message="contract mismatch",
        )
        self.identity=CanonicalIdentity("M1","W1",SHA)

    def test_builds_existing_aeos_work_item_shape(self):
        item=build_repair_work_item(
            identity=self.identity, failure=self.failure, repair_set=repair_set()
        )
        self.assertTrue(item.work_id.startswith("recon-repair-"))
        self.assertEqual(item.mission_id,"M1")
        self.assertEqual(item.baseline_sha,SHA)
        self.assertEqual(item.state,"QUEUED")
        self.assertEqual(item.attempt_count,0)
        self.assertEqual(item.failure_id,self.failure.fingerprint)
        payload=json.loads(item.intent)
        self.assertEqual(payload["type"],"RECON_REPAIR")
        self.assertEqual(payload["changed_files"],["tools/example.py"])

    def test_source_sha_mismatch_fails_closed(self):
        failure=ingest_failure(
            source_sha="c"*40, gate="gate-x", test="test-x",
            error_class="AssertionError", message="contract mismatch",
        )
        with self.assertRaisesRegex(ReconRepairMappingError,"source SHA"):
            build_repair_work_item(
                identity=self.identity, failure=failure, repair_set=repair_set()
            )

    def test_identity_is_not_replaced(self):
        item=build_repair_work_item(
            identity=self.identity, failure=self.failure, repair_set=repair_set()
        )
        self.assertEqual(item.mission_id,self.identity.mission_id)
        self.assertEqual(item.baseline_sha,self.identity.baseline_sha)

    def test_duplicate_dependency_fails_closed(self):
        with self.assertRaisesRegex(ReconRepairMappingError,"duplicate"):
            build_repair_work_item(
                identity=self.identity, failure=self.failure, repair_set=repair_set(),
                dependencies=("W2","W2"),
            )

if __name__=="__main__":
    unittest.main()
