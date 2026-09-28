from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from owner_special.research_os_friend.aeos_anti_circularity import evaluate_independence
from owner_special.research_os_friend.aeos_negative_space import scan_negative_space
from owner_special.research_os_friend.aeos_reality_scanner import scan_repository_reality
from owner_special.research_os_friend.aeos_temporal_freshness import evaluate_freshness


BASELINE = "a" * 40


class AeosRealityAssuranceBoundaryTests(unittest.TestCase):
    def test_repository_scanner_binds_real_head_and_file_fingerprints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "current").mkdir()
            (root / "current/contract.json").write_text("contract", encoding="utf-8")
            (root / "current/policy.json").write_text("policy", encoding="utf-8")
            (root / "source.py").write_text("source", encoding="utf-8")
            with patch("owner_special.research_os_friend.aeos_reality_scanner._git_head", return_value=BASELINE):
                observation = scan_repository_reality(
                    root=root,
                    baseline_sha=BASELINE,
                    contract_path="current/contract.json",
                    policy_path="current/policy.json",
                    source_paths=("source.py",),
                    observed_at="2026-09-09T00:00:00Z",
                )
            self.assertEqual(observation.observed_sha, BASELINE)
            self.assertEqual(observation.status, "VALID")
            self.assertIn("source_fingerprints", observation.facts)

    def test_freshness_is_deterministic_and_blocks_stale(self) -> None:
        fresh = evaluate_freshness(
            observed_at="2026-09-09T00:00:00Z",
            reference_time="2026-09-09T00:05:00Z",
            max_age_seconds=600,
        )
        stale = evaluate_freshness(
            observed_at="2026-09-09T00:00:00Z",
            reference_time="2026-09-09T01:00:01Z",
            max_age_seconds=3600,
        )
        self.assertTrue(fresh.fresh)
        self.assertEqual(stale.status, "STALE")

    def test_independence_rejects_shared_subject_source(self) -> None:
        decision = evaluate_independence(
            subject_id="implementation",
            verifier_id="verifier",
            subject_sources=("repo",),
            verifier_sources=("repo",),
            evidence_sources=("ci",),
        )
        self.assertFalse(decision.independent)
        self.assertEqual(decision.common_sources, ("repo",))

    def test_negative_space_requires_zero_blockers(self) -> None:
        report = scan_negative_space(
            counts={
                "required_work": 0,
                "recovery_work": 0,
                "unresolved_failures": 0,
                "unknown": 0,
                "stale": 0,
                "unverified": 0,
                "blocked_required": 0,
                "uncertified_integrations": 0,
                "orphan_work": 0,
                "unauthorized_mutations": 0,
            },
            forbidden_states=(),
            evidence_refs=("negative-space:1",),
        )
        self.assertTrue(report.passed)

    def test_negative_space_blocks_forbidden_state(self) -> None:
        report = scan_negative_space(
            counts={
                "required_work": 0,
                "recovery_work": 0,
                "unresolved_failures": 0,
                "unknown": 0,
                "stale": 0,
                "unverified": 0,
                "blocked_required": 0,
                "uncertified_integrations": 0,
                "orphan_work": 0,
                "unauthorized_mutations": 0,
            },
            forbidden_states=("UNKNOWN",),
            evidence_refs=("negative-space:2",),
        )
        self.assertFalse(report.passed)


if __name__ == "__main__":
    unittest.main()
