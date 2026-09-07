import copy
import unittest

from owner_special.research_os_friend.mission_control_final_gate_contract import (
    MissionControlFinalGateContract,
    MissionControlFinalGateContractError,
)


class MissionControlFinalGateContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = MissionControlFinalGateContract()
        self.readiness = {
            "schema": "research-os-mission-control-release-readiness/v1",
            "owner_id": "owner-special",
            "read_only": True,
            "source_authority": "authoritative-ci-gate-evidence",
            "overall_status": "READY_FOR_FINAL_GATE",
            "reason": "all projected required gates passed; Final Gate remains authoritative",
            "build_identity_status": "VERIFIED",
            "gates": {gate: "PASSED" for gate in self.contract.REQUIRED_GATES},
            "authority_boundary": "projection-only; no release authority",
        }

    def test_valid_readiness_becomes_final_gate_input(self):
        result = self.contract.validate(readiness=self.readiness)
        self.assertEqual(result["input_status"], "READY_FOR_FINAL_GATE")
        self.assertEqual(result["build_identity_status"], "VERIFIED")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["authority_boundary"], "contract-only; Final Gate remains authoritative")

    def test_never_reports_release(self):
        result = self.contract.validate(readiness=self.readiness)
        self.assertNotIn("release", result)
        self.assertNotEqual(result["input_status"], "RELEASE")

    def test_non_ready_status_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["overall_status"] = "PENDING"
        with self.assertRaises(MissionControlFinalGateContractError):
            self.contract.validate(readiness=readiness)

    def test_nonverified_identity_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["build_identity_status"] = "CONFLICT"
        with self.assertRaises(MissionControlFinalGateContractError):
            self.contract.validate(readiness=readiness)

    def test_missing_gate_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["gates"].pop("e2e")
        with self.assertRaises(MissionControlFinalGateContractError):
            self.contract.validate(readiness=readiness)

    def test_failed_gate_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["gates"]["release"] = "FAILED"
        with self.assertRaises(MissionControlFinalGateContractError):
            self.contract.validate(readiness=readiness)

    def test_action_authority_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["dispatch"] = True
        with self.assertRaises(MissionControlFinalGateContractError):
            self.contract.validate(readiness=readiness)

    def test_secret_like_value_is_rejected_before_projection(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["reason"] = "token=abc"
        with self.assertRaises(MissionControlFinalGateContractError):
            self.contract.validate(readiness=readiness)

    def test_input_is_not_mutated(self):
        readiness = copy.deepcopy(self.readiness)
        before = copy.deepcopy(readiness)
        self.contract.validate(readiness=readiness)
        self.assertEqual(readiness, before)

    def test_deterministic_output(self):
        first = self.contract.validate(readiness=self.readiness)
        second = self.contract.validate(readiness=self.readiness)
        self.assertEqual(first, second)

    def test_unsupported_schema_is_rejected(self):
        readiness = copy.deepcopy(self.readiness)
        readiness["schema"] = "wrong/schema"
        with self.assertRaises(MissionControlFinalGateContractError):
            self.contract.validate(readiness=readiness)


if __name__ == "__main__":
    unittest.main()
