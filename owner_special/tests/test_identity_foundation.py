import unittest

from owner_special.research_os_friend.identity_foundation import (
    CapturedIdentity,
    IdentityError,
    IdentityState,
    bind_evidence,
    evidence_is_fresh,
    lineage_id,
)


SHA_A = "a" * 40
SHA_B = "b" * 40


class IdentityFoundationTests(unittest.TestCase):
    def test_wait_capture_exact_sha(self):
        identity = CapturedIdentity.waiting(SHA_A, "run-123")
        self.assertEqual(identity.state, IdentityState.WAITING_FOR_SHA)
        captured = identity.capture(SHA_A)
        self.assertEqual(captured.state, IdentityState.CAPTURED)
        self.assertEqual(captured.captured_sha, SHA_A)

    def test_capture_mismatch_fails_closed(self):
        identity = CapturedIdentity.waiting(SHA_A, "run-123").capture(SHA_B)
        self.assertEqual(identity.state, IdentityState.SHA_MISMATCH)

    def test_captured_never_means_passed(self):
        identity = CapturedIdentity.waiting(SHA_A, "run-123").capture(SHA_A)
        self.assertEqual(identity.state, IdentityState.CAPTURED)
        self.assertNotEqual(identity.state, IdentityState.PASSED)

    def test_verify_requires_captured_identity(self):
        identity = CapturedIdentity.waiting(SHA_A, "run-123")
        with self.assertRaises(IdentityError):
            identity.verify(SHA_A)

    def test_verification_binds_to_exact_sha(self):
        identity = CapturedIdentity.waiting(SHA_A, "run-123").capture(SHA_A)
        verifying = identity.verify(SHA_A)
        self.assertEqual(verifying.state, IdentityState.VERIFYING)
        self.assertEqual(verifying.result(True).state, IdentityState.PASSED)

    def test_verification_mismatch_is_not_a_pass(self):
        identity = CapturedIdentity.waiting(SHA_A, "run-123").capture(SHA_A)
        self.assertEqual(identity.verify(SHA_B).state, IdentityState.SHA_MISMATCH)

    def test_bounded_wait_times_out(self):
        identity = CapturedIdentity.waiting(SHA_A, "run-123", max_attempts=1)
        self.assertEqual(identity.retry_wait().state, IdentityState.TIMEOUT)

    def test_stale_evidence_is_rejected(self):
        self.assertTrue(evidence_is_fresh({"commit_sha": SHA_A}, SHA_A))
        self.assertFalse(evidence_is_fresh({"commit_sha": SHA_A}, SHA_B))
        self.assertFalse(evidence_is_fresh({}, SHA_A))
        self.assertFalse(evidence_is_fresh({"commit_sha": "not-a-sha"}, SHA_A))

    def test_binding_preserves_identity_and_correlation(self):
        identity = CapturedIdentity.waiting(SHA_A, "run-123").capture(SHA_A)
        evidence = bind_evidence({"commit_sha": SHA_A, "status": "PASSED"}, identity)
        self.assertEqual(evidence["commit_sha"], SHA_A)
        self.assertEqual(evidence["run_correlation_id"], "run-123")

    def test_binding_blocks_stale_evidence(self):
        identity = CapturedIdentity.waiting(SHA_A, "run-123").capture(SHA_A)
        with self.assertRaises(IdentityError):
            bind_evidence({"commit_sha": SHA_B}, identity)

    def test_lineage_is_deterministic_and_sha_bound(self):
        first = lineage_id(SHA_A, "capture", "test")
        second = lineage_id(SHA_A, "capture", "test")
        other = lineage_id(SHA_B, "capture", "test")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)
        self.assertEqual(len(first), 64)

    def test_invalid_sha_is_rejected(self):
        with self.assertRaises(IdentityError):
            CapturedIdentity.waiting("A" * 40, "run-123")
        with self.assertRaises(IdentityError):
            lineage_id(SHA_A, "")


if __name__ == "__main__":
    unittest.main()
