from __future__ import annotations

import unittest

from owner_special.research_os_friend.aeos_certificate_chain import (
    CertificateChainError,
    issue_chain_certificate,
    verify_chain,
)
from owner_special.research_os_friend.aeos_constitutional_firewall import (
    ConstitutionalFirewallError,
    evaluate_constitutional_mutation,
)
from owner_special.research_os_friend.aeos_evidence_fabric import bind_evidence_bundle
from owner_special.research_os_friend.aeos_reality_boundary import (
    RealityObservationError,
    bind_reality_observation,
)


BASELINE = "a" * 40
CONTRACT = "b" * 64
POLICY = "c" * 64
PROVENANCE = "d" * 64
REFS = ("ci:1", "git:1")
FINGERPRINTS = {"ci:1": "e" * 64, "git:1": "f" * 64}
VERIFICATION_PROOF = "9" * 64


class Aeos100xRealityCertificateTests(unittest.TestCase):
    def test_reality_observation_is_bound_to_exact_sha(self) -> None:
        observation = bind_reality_observation(
            observation_id="obs-1",
            subject="main",
            baseline_sha=BASELINE,
            observed_sha=BASELINE,
            contract_sha256=CONTRACT,
            policy_sha256=POLICY,
            observed_at="2026-09-09T00:00:00Z",
            source="git-adapter",
            status="VALID",
            facts={"branch": "main"},
            evidence_refs=REFS,
        )
        self.assertEqual(observation.baseline_sha, BASELINE)
        self.assertEqual(observation.observed_sha, BASELINE)
        self.assertEqual(len(observation.evidence_digest), 64)

    def test_stale_observation_is_rejected(self) -> None:
        with self.assertRaises(RealityObservationError):
            bind_reality_observation(
                observation_id="obs-stale",
                subject="main",
                baseline_sha=BASELINE,
                observed_sha="1" * 40,
                contract_sha256=CONTRACT,
                policy_sha256=POLICY,
                observed_at="2026-09-09T00:00:00Z",
                source="git-adapter",
                status="VALID",
                facts={"branch": "main"},
                evidence_refs=REFS,
            )

    def test_evidence_bundle_root_is_deterministic(self) -> None:
        first = bind_evidence_bundle(
            bundle_id="bundle-1",
            baseline_sha=BASELINE,
            contract_sha256=CONTRACT,
            policy_sha256=POLICY,
            evidence_refs=REFS,
            source_fingerprints=FINGERPRINTS,
        )
        second = bind_evidence_bundle(
            bundle_id="bundle-2",
            baseline_sha=BASELINE,
            contract_sha256=CONTRACT,
            policy_sha256=POLICY,
            evidence_refs=("git:1", "ci:1"),
            source_fingerprints={"git:1": "f" * 64, "ci:1": "e" * 64},
        )
        self.assertEqual(first.evidence_root, second.evidence_root)
        self.assertEqual(first.evidence_refs, ("ci:1", "git:1"))

    def test_certificate_chain_links_previous_digest(self) -> None:
        first = issue_chain_certificate(
            certificate_id="c1",
            certificate_type="OBSERVATION",
            subject="main",
            baseline_sha=BASELINE,
            evidence_root="1" * 64,
            provenance_root=PROVENANCE,
            payload={"status": "VALID"},
            verification_proof=VERIFICATION_PROOF,
        )
        second = issue_chain_certificate(
            certificate_id="c2",
            certificate_type="VERIFICATION",
            subject="main",
            baseline_sha=BASELINE,
            evidence_root="1" * 64,
            provenance_root=PROVENANCE,
            payload={"status": "VERIFIED"},
            previous_certificate=first,
            verification_proof=VERIFICATION_PROOF,
        )
        self.assertTrue(verify_chain(first, second))
        self.assertEqual(second.previous_certificate_digest, first.payload_digest)

    def test_certificate_chain_rejects_mismatched_baseline(self) -> None:
        first = issue_chain_certificate(
            certificate_id="c1",
            certificate_type="OBSERVATION",
            subject="main",
            baseline_sha=BASELINE,
            evidence_root="1" * 64,
            provenance_root=PROVENANCE,
            payload={"status": "VALID"},
            verification_proof=VERIFICATION_PROOF,
        )
        with self.assertRaises(CertificateChainError):
            issue_chain_certificate(
                certificate_id="c2",
                certificate_type="VERIFICATION",
                subject="main",
                baseline_sha="2" * 40,
                evidence_root="1" * 64,
                provenance_root=PROVENANCE,
                payload={"status": "VERIFIED"},
                previous_certificate=first,
                verification_proof=VERIFICATION_PROOF,
            )

    def test_constitutional_mutation_requires_governance_proof(self) -> None:
        decision = evaluate_constitutional_mutation(
            paths=("current/AEOS_100X_CONTRACT.json",),
            mutation_kind="trust_anchor",
        )
        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_governance)

    def test_constitutional_mutation_does_not_accept_raw_boolean(self) -> None:
        with self.assertRaises(ConstitutionalFirewallError):
            evaluate_constitutional_mutation(
                paths=("current/AEOS_100X_CONTRACT.json",),
                mutation_kind="trust_anchor",
                governance_proof=True,  # type: ignore[arg-type]
            )

    def test_unprotected_mutation_remains_bounded(self) -> None:
        decision = evaluate_constitutional_mutation(
            paths=("owner_special/research_os_friend/example.py",),
            mutation_kind="implementation",
        )
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.requires_governance)


if __name__ == "__main__":
    unittest.main()
