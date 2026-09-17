import unittest

from owner_special.research_os_friend.autobot_governance import ReconState
from owner_special.research_os_friend.recon_failure import FailureKind, ingest_failure


class ReconFailureTests(unittest.TestCase):
    def test_code_failure_enters_recon_as_code_defect(self):
        failure = ingest_failure(
            source_sha="d115518c0d904c2a10b992edd8335ca7d15d0d99",
            gate="Provenance Evidence Gate",
            test="tools.test_validate_provenance_evidence",
            error_class="ModuleNotFoundError",
            message="No module named 'validate_provenance_evidence'",
        )
        self.assertEqual(failure.kind, FailureKind.CODE_DEFECT)
        self.assertEqual(failure.state, ReconState.CODE_DEFECT)
        self.assertEqual(len(failure.fingerprint), 64)

    def test_same_failure_identity_has_same_fingerprint(self):
        args = dict(
            source_sha="d115518c0d904c2a10b992edd8335ca7d15d0d99",
            gate="Provenance Evidence Gate",
            test="tools.test_validate_provenance_evidence",
            error_class="ModuleNotFoundError",
            message="No module named 'validate_provenance_evidence'",
        )
        self.assertEqual(ingest_failure(**args).fingerprint, ingest_failure(**args).fingerprint)

    def test_integrity_failure_cannot_be_downgraded_to_retry(self):
        failure = ingest_failure(
            source_sha="d115518c0d904c2a10b992edd8335ca7d15d0d99",
            gate="Provenance Evidence Gate",
            test="target-bound-root-verification",
            error_class="ValueError",
            message="root digest mismatch",
            integrity_signal=True,
        )
        self.assertEqual(failure.kind, FailureKind.INTEGRITY_FAILURE)
        self.assertEqual(failure.state, ReconState.INTEGRITY_FAILURE)


if __name__ == "__main__":
    unittest.main()
