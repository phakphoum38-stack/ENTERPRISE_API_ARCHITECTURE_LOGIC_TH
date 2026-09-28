import copy
import unittest

from owner_special.research_os_friend.mission_control_final_gate_boundary import (
    MissionControlFinalGateBoundary,
    MissionControlFinalGateBoundaryError,
)


class MissionControlFinalGateBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.boundary = MissionControlFinalGateBoundary()
        self.readiness = {
            "schema": "research-os-mission-control-release-readiness/v1",
            "owner_id": "owner-special",
            "read_only": True,
            "source_authority": "authoritative-ci-gate-evidence",
            "overall_status": "READY_FOR_FINAL_GATE",
            "reason": "all projected required gates passed; Final Gate remains authoritative",
            "build_identity_status": "VERIFIED",
            "gates": {
                gate: "PASSED"
                for gate in (
                    "architecture",
                    "security_boundary",
                    "generation",
                    "external_tool",
                    "api_contract",
                    "e2e",
                    "release",
                )
            },
            "authority_boundary": "projection-only; no release authority",
        }

    def test_valid_projection_crosses_boundary(self):
        result = self.boundary.validate(readiness=self.readiness)
        self.assertEqual(result["input_status"], "READY_FOR_FINAL_GATE")
        self.assertTrue(result["read_only"])
        self.assertNotIn("release", result)

    def test_invalid_source_authority_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["source_authority"] = "manual-evidence"
        with self.assertRaises(MissionControlFinalGateBoundaryError):
            self.boundary.validate(readiness=readiness)

    def test_nested_action_authority_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["metadata"] = {"dispatch": True}
        with self.assertRaises(MissionControlFinalGateBoundaryError):
            self.boundary.validate(readiness=readiness)

    def test_nested_secret_like_value_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["metadata"] = {"note": "token=abc"}
        with self.assertRaises(MissionControlFinalGateBoundaryError):
            self.boundary.validate(readiness=readiness)

    def test_input_is_not_mutated(self):
        readiness = copy.deepcopy(self.readiness)
        before = copy.deepcopy(readiness)
        self.boundary.validate(readiness=readiness)
        self.assertEqual(readiness, before)

    def test_output_has_no_action_authority(self):
        result = self.boundary.validate(readiness=self.readiness)
        self.assertTrue(set(result).isdisjoint(self.boundary.ACTION_FIELDS))


if __name__ == "__main__":
    unittest.main()
