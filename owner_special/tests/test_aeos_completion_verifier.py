import unittest

from owner_special.research_os_friend.aeos_completion_verifier import (
    CompletionVerificationError,
    verify_completion_observation,
)
from owner_special.research_os_friend.aeos_stop_controller import (
    build_authoritative_stop_proof,
)


BASELINE = "a" * 40
SCAN_ORDER = (
    "mission_scan", "dependency_scan", "queue_scan", "recovery_scan",
    "pull_request_scan", "branch_scan", "ci_scan", "failure_scan",
    "unknown_scan", "stale_scan", "evidence_scan", "provenance_scan",
    "governance_scan", "main_scan", "final_rescan",
)
COUNTS = {
    "required_work": 0,
    "recovery_work": 0,
    "unresolved_failures": 0,
    "unknown": 0,
    "stale": 0,
    "unverified": 0,
    "blocked_required": 0,
    "uncertified_integrations": 0,
    "main_verified": True,
    "final_rescan": True,
}


def valid_payload():
    return {
        "scan_order": SCAN_ORDER,
        "scans": {
            name: {"status": "PASS", "evidence_refs": (f"EV-{index:03d}",)}
            for index, name in enumerate(SCAN_ORDER, 1)
        },
        "observations": dict(COUNTS),
    }


class CompletionVerifierTests(unittest.TestCase):
    def test_valid_observation_is_verified(self):
        result = verify_completion_observation(
            baseline_sha=BASELINE,
            observed_sha=BASELINE,
            scan_results=valid_payload(),
            evidence_refs=("EV-ROOT",),
        )
        self.assertTrue(result.verified)
        self.assertEqual(result.baseline_sha, BASELINE)
        self.assertEqual(len(result.evidence_digest), 64)

    def test_stale_observation_is_rejected(self):
        with self.assertRaises(CompletionVerificationError):
            verify_completion_observation(
                baseline_sha=BASELINE,
                observed_sha="b" * 40,
                scan_results=valid_payload(),
                evidence_refs=("EV-ROOT",),
            )

    def test_missing_scan_is_rejected(self):
        payload = valid_payload()
        del payload["scans"]["governance_scan"]
        with self.assertRaises(CompletionVerificationError):
            verify_completion_observation(
                baseline_sha=BASELINE,
                observed_sha=BASELINE,
                scan_results=payload,
                evidence_refs=("EV-ROOT",),
            )

    def test_unknown_scan_status_cannot_pass(self):
        payload = valid_payload()
        payload["scans"]["unknown_scan"] = {
            "status": "UNKNOWN", "evidence_refs": ("EV-009",)
        }
        with self.assertRaises(CompletionVerificationError):
            verify_completion_observation(
                baseline_sha=BASELINE,
                observed_sha=BASELINE,
                scan_results=payload,
                evidence_refs=("EV-ROOT",),
            )

    def test_string_boolean_is_rejected(self):
        payload = valid_payload()
        payload["observations"]["main_verified"] = "true"
        with self.assertRaises(CompletionVerificationError):
            verify_completion_observation(
                baseline_sha=BASELINE,
                observed_sha=BASELINE,
                scan_results=payload,
                evidence_refs=("EV-ROOT",),
            )

    def test_authoritative_stop_proof_requires_verified_observation(self):
        result = verify_completion_observation(
            baseline_sha=BASELINE,
            observed_sha=BASELINE,
            scan_results=valid_payload(),
            evidence_refs=("EV-ROOT",),
        )
        proof = build_authoritative_stop_proof(result)
        self.assertEqual(proof["status"], "PASS")
        self.assertTrue(proof["independently_verified"])
        self.assertEqual(proof["baseline_sha"], BASELINE)
        self.assertEqual(proof["terminal_state"], "CERTIFIED_IDLE")


if __name__ == "__main__":
    unittest.main()
