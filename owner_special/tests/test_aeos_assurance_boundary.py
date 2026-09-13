from __future__ import annotations

import unittest

from owner_special.research_os_friend.aeos_anti_circularity import evaluate_independence
from owner_special.research_os_friend.aeos_assurance_boundary import (
    AssuranceBoundaryError,
    build_verified_completion_observation,
)
from owner_special.research_os_friend.aeos_negative_space import scan_negative_space
from owner_special.research_os_friend.aeos_reality_boundary import bind_reality_observation
from owner_special.research_os_friend.aeos_temporal_freshness import evaluate_freshness


BASELINE = "a" * 40
CONTRACT = "b" * 64
POLICY = "c" * 64
REFS = ("reality:1", "negative-space:1", "verifier:1")
SCANS = (
    "mission_scan", "dependency_scan", "queue_scan", "recovery_scan",
    "pull_request_scan", "branch_scan", "ci_scan", "failure_scan",
    "unknown_scan", "stale_scan", "evidence_scan", "provenance_scan",
    "governance_scan", "main_scan", "final_rescan",
)


def reality():
    return bind_reality_observation(
        observation_id="obs-1",
        subject="main",
        baseline_sha=BASELINE,
        observed_sha=BASELINE,
        contract_sha256=CONTRACT,
        policy_sha256=POLICY,
        observed_at="2026-09-09T00:00:00Z",
        source="repository-reality-scanner/v1",
        status="VALID",
        facts={"head_sha": BASELINE},
        evidence_refs=("reality:1",),
    )


def scans():
    return {
        "scan_order": SCANS,
        "scans": {name: {"status": "PASS", "evidence_refs": (f"scan:{name}",)} for name in SCANS},
        "observations": {
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
        },
    }


def negative_space():
    return scan_negative_space(
        counts={
            "required_work": 0, "recovery_work": 0, "unresolved_failures": 0,
            "unknown": 0, "stale": 0, "unverified": 0, "blocked_required": 0,
            "uncertified_integrations": 0, "orphan_work": 0,
            "unauthorized_mutations": 0,
        },
        forbidden_states=(),
        evidence_refs=("negative-space:1",),
    )


class AeosAssuranceBoundaryTests(unittest.TestCase):
    def test_integrated_boundary_produces_verified_observation(self) -> None:
        observation = build_verified_completion_observation(
            reality=reality(),
            freshness=evaluate_freshness(
                observed_at="2026-09-09T00:00:00Z",
                reference_time="2026-09-09T00:00:10Z",
                max_age_seconds=60,
            ),
            independence=evaluate_independence(
                subject_id="builder",
                verifier_id="independent-verifier",
                subject_sources=("builder-runtime",),
                verifier_sources=("verification-runtime",),
                evidence_sources=("external-ci",),
            ),
            negative_space=negative_space(),
            scan_results=scans(),
            evidence_refs=REFS,
        )
        self.assertTrue(observation.verified)
        self.assertTrue(observation.is_verifier_issued())
        self.assertEqual(observation.baseline_sha, BASELINE)

    def test_integrated_boundary_rejects_stale_reality(self) -> None:
        with self.assertRaises(AssuranceBoundaryError):
            build_verified_completion_observation(
                reality=reality(),
                freshness=evaluate_freshness(
                    observed_at="2026-09-09T00:00:00Z",
                    reference_time="2026-09-10T00:00:00Z",
                    max_age_seconds=60,
                ),
                independence=evaluate_independence(
                    subject_id="builder",
                    verifier_id="independent-verifier",
                    subject_sources=("builder-runtime",),
                    verifier_sources=("verification-runtime",),
                    evidence_sources=("external-ci",),
                ),
                negative_space=negative_space(),
                scan_results=scans(),
                evidence_refs=REFS,
            )

    def test_integrated_boundary_rejects_circular_verifier(self) -> None:
        independence = evaluate_independence(
            subject_id="builder",
            verifier_id="builder",
            subject_sources=("builder-runtime",),
            verifier_sources=("builder-runtime",),
            evidence_sources=("external-ci",),
        )
        with self.assertRaises(AssuranceBoundaryError):
            build_verified_completion_observation(
                reality=reality(),
                freshness=evaluate_freshness(
                    observed_at="2026-09-09T00:00:00Z",
                    reference_time="2026-09-09T00:00:10Z",
                    max_age_seconds=60,
                ),
                independence=independence,
                negative_space=negative_space(),
                scan_results=scans(),
                evidence_refs=REFS,
            )

    def test_integrated_boundary_rejects_negative_space_blocker(self) -> None:
        blocked = scan_negative_space(
            counts={
                "required_work": 1, "recovery_work": 0, "unresolved_failures": 0,
                "unknown": 0, "stale": 0, "unverified": 0, "blocked_required": 0,
                "uncertified_integrations": 0, "orphan_work": 0,
                "unauthorized_mutations": 0,
            },
            forbidden_states=(),
            evidence_refs=("negative-space:blocked",),
        )
        with self.assertRaises(AssuranceBoundaryError):
            build_verified_completion_observation(
                reality=reality(),
                freshness=evaluate_freshness(
                    observed_at="2026-09-09T00:00:00Z",
                    reference_time="2026-09-09T00:00:10Z",
                    max_age_seconds=60,
                ),
                independence=evaluate_independence(
                    subject_id="builder",
                    verifier_id="independent-verifier",
                    subject_sources=("builder-runtime",),
                    verifier_sources=("verification-runtime",),
                    evidence_sources=("external-ci",),
                ),
                negative_space=blocked,
                scan_results=scans(),
                evidence_refs=REFS,
            )


if __name__ == "__main__":
    unittest.main()
