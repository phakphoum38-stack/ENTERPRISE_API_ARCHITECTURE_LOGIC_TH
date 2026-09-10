from __future__ import annotations

import unittest

from owner_special.research_os_friend.aeos_runtime_certificate import (
    RuntimeCertificateError,
    certify_runtime_result,
)


BASELINE = "a" * 40
HASH = "b" * 64
EVIDENCE = ("EV-001",)
PROOF = "9" * 64


def make_certificate(**overrides):
    values = {
        "certificate_id": "CERT-001",
        "baseline_sha": BASELINE,
        "observed_sha": BASELINE,
        "contract_sha256": HASH,
        "policy_sha256": HASH,
        "evidence_root": HASH,
        "provenance_root": HASH,
        "test_manifest_sha256": HASH,
        "result": {"status": "PASS"},
        "evidence_refs": EVIDENCE,
        "verification_proof": PROOF,
    }
    values.update(overrides)
    return certify_runtime_result(**values)


class RuntimeCertificateBoundaryTests(unittest.TestCase):
    def test_valid_result_is_bound(self):
        certificate = make_certificate()
        self.assertEqual(certificate.baseline_sha, BASELINE)
        self.assertEqual(len(certificate.result_digest), 64)
        self.assertEqual(certificate.verification_proof, PROOF)

    def test_stale_runtime_result_is_rejected(self):
        with self.assertRaises(RuntimeCertificateError):
            make_certificate(observed_sha="c" * 40)

    def test_unverified_runtime_result_is_rejected(self):
        with self.assertRaises((RuntimeCertificateError, TypeError)):
            make_certificate(verification_proof=True)

    def test_missing_result_is_rejected(self):
        with self.assertRaises(RuntimeCertificateError):
            make_certificate(result={})

    def test_invalid_contract_binding_is_rejected(self):
        with self.assertRaises(RuntimeCertificateError):
            make_certificate(contract_sha256="bad")

    def test_missing_evidence_reference_is_rejected(self):
        with self.assertRaises(RuntimeCertificateError):
            make_certificate(evidence_refs=())

    def test_missing_verification_proof_is_rejected(self):
        with self.assertRaises((RuntimeCertificateError, TypeError)):
            values = {
                "certificate_id": "CERT-001",
                "baseline_sha": BASELINE,
                "observed_sha": BASELINE,
                "contract_sha256": HASH,
                "policy_sha256": HASH,
                "evidence_root": HASH,
                "provenance_root": HASH,
                "test_manifest_sha256": HASH,
                "result": {"status": "PASS"},
                "evidence_refs": EVIDENCE,
            }
            certify_runtime_result(**values)


if __name__ == "__main__":
    unittest.main()
