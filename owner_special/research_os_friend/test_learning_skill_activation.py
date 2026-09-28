from __future__ import annotations

import hashlib
import json
import unittest

from owner_special.research_os_friend.learning_skill_activation import (
    LearnedSkillActivationBoundary,
    LearnedSkillActivationError,
    LearnedSkillActivationRequest,
)


class LearnedSkillActivationBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = LearnedSkillActivationBoundary()
        self.skill = {
            "name": "bounded-research",
            "goal": "collect bounded research evidence",
            "procedure": ["inspect", "compare", "summarize"],
            "evidence": ["evidence:bounded"],
            "confidence": 0.91,
            "status": "approved",
            "version": 1,
        }
        unsigned = {
            "schema": "research-os-learning-skill-consumption/v1",
            "owner": "owner_special",
            "skill_name": "bounded-research",
            "skill_version": 1,
            "registry_fingerprint": "a" * 64,
            "correlation_id": "corr-h23",
            "skill": self.skill,
            "consumption_state": "READY_FOR_GOVERNED_USE",
            "execution_authority": "H24",
            "read_only": True,
            "authority": "none",
        }
        canonical = json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        self.consumption = dict(unsigned)
        self.consumption["consumption_fingerprint"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.request = LearnedSkillActivationRequest(
            owner="owner_special",
            skill_name="bounded-research",
            skill_version=1,
            consumption_fingerprint=self.consumption["consumption_fingerprint"],
            activation_id="activation-h24-001",
        )

    def test_ready_consumption_creates_activation(self) -> None:
        result = self.boundary.activate(self.request, self.consumption)
        self.assertEqual(result["schema"], "research-os-learning-skill-activation/v1")
        self.assertEqual(result["activation_state"], "READY_FOR_H25")
        self.assertEqual(result["execution_authority"], "H25")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["authority"], "none")

    def test_consumption_state_is_required(self) -> None:
        value = dict(self.consumption)
        value["consumption_state"] = "NOT_READY"
        with self.assertRaises(LearnedSkillActivationError):
            self.boundary.activate(self.request, value)

    def test_authority_contract_is_required(self) -> None:
        value = dict(self.consumption)
        value["authority"] = "H24"
        with self.assertRaises(LearnedSkillActivationError):
            self.boundary.activate(self.request, value)

    def test_identity_mismatch_is_rejected(self) -> None:
        request = LearnedSkillActivationRequest(
            owner="owner_special",
            skill_name="other",
            skill_version=1,
            consumption_fingerprint=self.consumption["consumption_fingerprint"],
            activation_id="activation-h24-001",
        )
        with self.assertRaises(LearnedSkillActivationError):
            self.boundary.activate(request, self.consumption)

    def test_unsafe_skill_is_rejected(self) -> None:
        value = dict(self.consumption)
        value["skill"] = dict(self.skill, procedure=["execute subprocess"])
        with self.assertRaises(LearnedSkillActivationError):
            self.boundary.activate(self.request, value)

    def test_activation_id_is_bounded(self) -> None:
        request = LearnedSkillActivationRequest(
            owner="owner_special",
            skill_name="bounded-research",
            skill_version=1,
            consumption_fingerprint=self.consumption["consumption_fingerprint"],
            activation_id="secret-token",
        )
        with self.assertRaises(LearnedSkillActivationError):
            self.boundary.activate(request, self.consumption)


if __name__ == "__main__":
    unittest.main()
