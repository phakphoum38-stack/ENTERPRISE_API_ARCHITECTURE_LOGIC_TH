import json
import tempfile
import unittest
from pathlib import Path

from tools.platform_operationalization import PlatformOperationalization


class PlatformOperationalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.op = PlatformOperationalization()

    def test_snapshot_is_source_pinned_and_complete(self):
        snapshot = self.op.snapshot(
            active_work=["platform-operationalization"],
            deferred_work=["flutter_windows_analyze_test_failures"],
            decisions=["platform_is_reusable_root"],
            verified_truths=["final_gate_is_release_authority"],
            evidence_refs=["current/PLATFORM_OPERATIONALIZATION_CONTRACT.json"],
        )
        result = self.op.validate_snapshot(snapshot)
        self.assertEqual(result["status"], "PASS")
        self.assertRegex(result["source_sha"], r"^[0-9a-f]{40}$")
        self.assertEqual(result["deferred_work"], ["flutter_windows_analyze_test_failures"])

    def test_snapshot_sha_mismatch_holds(self):
        snapshot = self.op.snapshot()
        snapshot["source_sha"] = "0" * 40
        self.assertEqual(self.op.validate_snapshot(snapshot)["status"], "HOLD")

    def test_unknown_and_authority_violation_hold(self):
        snapshot = self.op.snapshot(unknowns=["unresolved"])
        snapshot["authority_boundaries"]["platform_may_release"] = True
        result = self.op.validate_snapshot(snapshot)
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("unknowns_present", result["failures"])
        self.assertIn("authority_boundary_violation", result["failures"])

    def test_impact_guard_is_explicit(self):
        result = self.op.impact_guard("runner")
        self.assertIn("impact", result)
        self.assertIn("contracts", result["impact"])
        self.assertIn("final_gate", result["impact"])

    def test_lifecycle_is_fail_closed(self):
        self.assertEqual(self.op.lifecycle_classify("DEFERRED")["action"], "PRESERVE_AND_RETURN")
        self.assertEqual(self.op.lifecycle_classify("CONFLICT")["action"], "REJECT_AND_RELEASE")
        self.assertEqual(self.op.lifecycle_classify("UNKNOWN")["status"], "HOLD")
        self.assertEqual(self.op.lifecycle_classify("bogus")["status"], "HOLD")

    def test_evidence_reconciliation(self):
        result = self.op.evidence_reconcile(["current/PLATFORM_OPERATIONALIZATION_CONTRACT.json"])
        self.assertEqual(result["status"], "PASS")
        missing = self.op.evidence_reconcile(["current/does-not-exist.json"])
        self.assertEqual(missing["status"], "HOLD")

    def test_resume_preserves_deferred_work(self):
        snapshot = self.op.snapshot(deferred_work=["deferred-a"])
        result = self.op.resume(snapshot)
        self.assertEqual(result["status"], "READY_FOR_RECON")
        self.assertEqual(result["deferred_work"], ["deferred-a"])


if __name__ == "__main__":
    unittest.main()
