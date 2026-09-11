import unittest

from tools.aeos_assurance_proof import issue_assurance_proof, verify_assurance_proof


class TestAssuranceProof(unittest.TestCase):
    def _proof(self):
        return issue_assurance_proof(
            source_sha="a" * 40,
            iteration_id="iteration-1",
            evidence_ids=("b" * 64,),
            provenance_verified=True,
            evidence_integrity_verified=True,
            forensic_result="PASS",
            independent_review="PASS",
            recommended_decision="APPROVE",
        )

    def test_valid_proof_is_target_bound(self):
        verify_assurance_proof(
            self._proof(),
            source_sha="a" * 40,
            iteration_id="iteration-1",
            evidence_ids=("b" * 64,),
        )

    def test_tampered_seal_is_rejected(self):
        proof = self._proof()
        proof["verification_seal"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "proof_verification_seal_invalid"):
            verify_assurance_proof(proof, source_sha="a" * 40, iteration_id="iteration-1", evidence_ids=("b" * 64,))

    def test_wrong_target_sha_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "proof_source_sha_mismatch"):
            verify_assurance_proof(self._proof(), source_sha="c" * 40, iteration_id="iteration-1", evidence_ids=("b" * 64,))

    def test_string_boolean_cannot_mint_proof(self):
        with self.assertRaisesRegex(ValueError, "proof_provenance_not_verified"):
            issue_assurance_proof(
                source_sha="a" * 40,
                iteration_id="iteration-1",
                evidence_ids=("b" * 64,),
                provenance_verified="true",
                evidence_integrity_verified=True,
                forensic_result="PASS",
                independent_review="PASS",
                recommended_decision="APPROVE",
            )


if __name__ == "__main__":
    unittest.main()
