from __future__ import annotations

import hashlib
import json
import unittest

from owner_special.research_os_friend.learning_skill_consumption import (
    LearnedSkillConsumptionBoundary,
    LearnedSkillConsumptionError,
    LearnedSkillConsumptionRequest,
)


class LearnedSkillConsumptionBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = LearnedSkillConsumptionBoundary()
        self.snapshot = (
            {
                "name": "bounded-research",
                "goal": "collect bounded research evidence",
                "procedure": ("inspect", "compare", "summarize"),
                "evidence": ("evidence:bounded",),
                "confidence": 0.91,
                "status": "approved",
                "version": 1,
                "metadata": {"owner": "owner_special"},
            },
        )
        registry_fingerprint = hashlib.sha256(
            json.dumps(self.snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        self.request = LearnedSkillConsumptionRequest(
            owner="owner_special",
            skill_name="bounded-research",
            expected_version=1,
            registry_fingerprint=registry_fingerprint,
            correlation_id="corr-h23",
        )

    def test_approved_skill_is_prepared_without_execution(self) -> None:
        result = self.boundary.prepare(self.request, self.snapshot)
        self.assertEqual(result["schema"], "research-os-learning-skill-consumption/v1")
        self.assertEqual(result["consumption_state"], "READY_FOR_GOVERNED_USE")
        self.assertEqual(result["execution_authority"], "H24")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["authority"], "none")

    def test_missing_skill_is_rejected(self) -> None:
        request = LearnedSkillConsumptionRequest(
            owner="owner_special",
            skill_name="missing",
            expected_version=1,
            registry_fingerprint=self.request.registry_fingerprint,
            correlation_id="corr-h23",
        )
        with self.assertRaises(LearnedSkillConsumptionError):
            self.boundary.prepare(request, self.snapshot)

    def test_unapproved_skill_is_rejected(self) -> None:
        snapshot = (dict(self.snapshot[0], status="candidate"),)
        with self.assertRaises(LearnedSkillConsumptionError):
            self.boundary.prepare(self.request, snapshot)

    def test_version_mismatch_is_rejected(self) -> None:
        request = LearnedSkillConsumptionRequest(
            owner="owner_special",
            skill_name="bounded-research",
            expected_version=2,
            registry_fingerprint=self.request.registry_fingerprint,
            correlation_id="corr-h23",
        )
        with self.assertRaises(LearnedSkillConsumptionError):
            self.boundary.prepare(request, self.snapshot)

    def test_registry_fingerprint_mismatch_is_rejected(self) -> None:
        request = LearnedSkillConsumptionRequest(
            owner="owner_special",
            skill_name="bounded-research",
            expected_version=1,
            registry_fingerprint="f" * 64,
            correlation_id="corr-h23",
        )
        with self.assertRaises(LearnedSkillConsumptionError):
            self.boundary.prepare(request, self.snapshot)

    def test_unsafe_skill_is_rejected(self) -> None:
        snapshot = (dict(self.snapshot[0], procedure=("execute subprocess",)),)
        registry_fingerprint = hashlib.sha256(
            json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()
        request = LearnedSkillConsumptionRequest(
            owner="owner_special",
            skill_name="bounded-research",
            expected_version=1,
            registry_fingerprint=registry_fingerprint,
            correlation_id="corr-h23",
        )
        with self.assertRaises(LearnedSkillConsumptionError):
            self.boundary.prepare(request, snapshot)

    def test_snapshot_must_be_immutable_tuple(self) -> None:
        with self.assertRaises(LearnedSkillConsumptionError):
            self.boundary.prepare(self.request, list(self.snapshot))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
