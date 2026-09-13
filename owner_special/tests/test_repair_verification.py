import unittest

from owner_special.research_os_friend.repair_verification import (
    RepairVerificationError,
    VerificationState,
    verify_repair_evidence,
)


SOURCE = "1111111111111111111111111111111111111111"
REPAIR = "2222222222222222222222222222222222222222"
CORRELATION = "h9-test-001"
PROVENANCE = "a" * 64


class RepairVerificationTests(unittest.TestCase):
    def test_explicit_matching_ci_pass_is_accepted(self):
        result = verify_repair_evidence(
            source_sha=SOURCE,
            repair_sha=REPAIR,
            correlation_id=CORRELATION,
            evidence={"status": "PASS", "commit_sha": REPAIR, "correlation_id": CORRELATION},
            provenance_fingerprint=PROVENANCE,
        )
        self.assertEqual(result.state, VerificationState.PASSED)

    def test_same_sha_is_rejected(self):
        with self.assertRaises(RepairVerificationError):
            verify_repair_evidence(
                source_sha=SOURCE,
                repair_sha=SOURCE,
                correlation_id=CORRELATION,
                evidence={"status": "PASS", "commit_sha": SOURCE, "correlation_id": CORRELATION},
                provenance_fingerprint=PROVENANCE,
            )

    def test_stale_sha_is_rejected(self):
        with self.assertRaises(RepairVerificationError):
            verify_repair_evidence(
                source_sha=SOURCE,
                repair_sha=REPAIR,
                correlation_id=CORRELATION,
                evidence={"status": "PASS", "commit_sha": SOURCE, "correlation_id": CORRELATION},
                provenance_fingerprint=PROVENANCE,
            )

    def test_wrong_correlation_is_rejected(self):
        with self.assertRaises(RepairVerificationError):
            verify_repair_evidence(
                source_sha=SOURCE,
                repair_sha=REPAIR,
                correlation_id=CORRELATION,
                evidence={"status": "PASS", "commit_sha": REPAIR, "correlation_id": "other"},
                provenance_fingerprint=PROVENANCE,
            )

    def test_missing_provenance_is_rejected(self):
        with self.assertRaises(RepairVerificationError):
            verify_repair_evidence(
                source_sha=SOURCE,
                repair_sha=REPAIR,
                correlation_id=CORRELATION,
                evidence={"status": "PASS", "commit_sha": REPAIR, "correlation_id": CORRELATION},
                provenance_fingerprint=None,
            )

    def test_fail_does_not_become_pass(self):
        result = verify_repair_evidence(
            source_sha=SOURCE,
            repair_sha=REPAIR,
            correlation_id=CORRELATION,
            evidence={"status": "FAIL", "commit_sha": REPAIR, "correlation_id": CORRELATION},
            provenance_fingerprint=PROVENANCE,
        )
        self.assertEqual(result.state, VerificationState.FAILED)

    def test_secret_like_evidence_is_rejected(self):
        with self.assertRaises(RepairVerificationError):
            verify_repair_evidence(
                source_sha=SOURCE,
                repair_sha=REPAIR,
                correlation_id=CORRELATION,
                evidence={"api_key": "blocked"},
                provenance_fingerprint=PROVENANCE,
            )

    def test_fingerprint_is_deterministic(self):
        kwargs = dict(
            source_sha=SOURCE,
            repair_sha=REPAIR,
            correlation_id=CORRELATION,
            evidence={"status": "FAIL", "commit_sha": REPAIR, "correlation_id": CORRELATION},
            provenance_fingerprint=PROVENANCE,
        )
        self.assertEqual(verify_repair_evidence(**kwargs).fingerprint, verify_repair_evidence(**kwargs).fingerprint)


if __name__ == "__main__":
    unittest.main()
