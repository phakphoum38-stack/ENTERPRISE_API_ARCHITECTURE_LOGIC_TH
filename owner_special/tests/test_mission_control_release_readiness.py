import copy
import unittest

from owner_special.research_os_friend.mission_control_release_readiness import (
    MissionControlReleaseReadinessError,
    MissionControlReleaseReadinessProjection,
)


class MissionControlReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.projection = MissionControlReleaseReadinessProjection()
        self.passed = {gate: {"passed": True} for gate in self.projection.REQUIRED_GATES}

    def test_all_passed_is_ready_for_final_gate_not_released(self):
        result = self.projection.snapshot(owner_id="owner-special", gate_evidence=self.passed, build_identity_status="VERIFIED")
        self.assertEqual(result["overall_status"], "READY_FOR_FINAL_GATE")
        self.assertEqual(result["authority_boundary"], "projection-only; no release authority")
        self.assertNotIn("release", result)

    def test_missing_gate_is_pending(self):
        evidence = dict(self.passed)
        evidence.pop("e2e")
        result = self.projection.snapshot(owner_id="owner-special", gate_evidence=evidence, build_identity_status="VERIFIED")
        self.assertEqual(result["overall_status"], "PENDING")
        self.assertEqual(result["gates"]["e2e"], "PENDING")

    def test_failed_gate_blocks(self):
        evidence = copy.deepcopy(self.passed)
        evidence["release"] = {"passed": False}
        result = self.projection.snapshot(owner_id="owner-special", gate_evidence=evidence, build_identity_status="VERIFIED")
        self.assertEqual(result["overall_status"], "BLOCKED")

    def test_nonverified_identity_blocks(self):
        result = self.projection.snapshot(owner_id="owner-special", gate_evidence=self.passed, build_identity_status="CONFLICT")
        self.assertEqual(result["overall_status"], "BLOCKED")

    def test_input_is_not_mutated(self):
        evidence = copy.deepcopy(self.passed)
        before = copy.deepcopy(evidence)
        self.projection.snapshot(owner_id="owner-special", gate_evidence=evidence)
        self.assertEqual(evidence, before)

    def test_secret_like_value_is_rejected(self):
        evidence = copy.deepcopy(self.passed)
        evidence["architecture"] = {"passed": True, "note": "token=abc"}
        with self.assertRaises(MissionControlReleaseReadinessError):
            self.projection.snapshot(owner_id="owner-special", gate_evidence=evidence)

    def test_action_authority_fields_are_not_exposed(self):
        result = self.projection.snapshot(owner_id="owner-special", gate_evidence=self.passed)
        self.assertTrue(result["read_only"])
        self.assertTrue(set(result).isdisjoint(self.projection.ACTION_FIELDS))

    def test_oversized_owner_is_rejected(self):
        with self.assertRaises(MissionControlReleaseReadinessError):
            self.projection.snapshot(owner_id="x" * (self.projection.MAX_STRING + 1), gate_evidence=self.passed)


if __name__ == "__main__":
    unittest.main()
