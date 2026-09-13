from __future__ import annotations

import hashlib
import json
import unittest

from owner_special.research_os_friend.learning_skill_registry_boundary import (
    LearnedSkillRegistryBoundary,
    LearnedSkillRegistryBoundaryError,
    LearnedSkillRegistryRequest,
)
from owner_special.research_os_friend.self_learning.registry import LearnedSkillRegistry


class LearnedSkillRegistryBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.boundary = LearnedSkillRegistryBoundary()
        self.registry = LearnedSkillRegistry()
        self.record_fingerprint = "a" * 64
        self.candidate = {
            "name": "bounded-research",
            "goal": "collect bounded research evidence",
            "procedure": ["inspect", "compare", "summarize"],
            "evidence": ["evidence:bounded"],
            "confidence": 0.91,
            "version": 1,
            "metadata": {"owner": "owner_special"},
        }
        unsigned = {
            "schema": "research-os-learning-promotion-receipt/v1",
            "owner": "owner_special",
            "record_fingerprint": self.record_fingerprint,
            "promotion_authority": "H10",
            "approved": True,
            "read_only": True,
            "authority": "none",
            "candidate": self.candidate,
        }
        self.receipt = dict(unsigned)
        self.receipt["receipt_fingerprint"] = hashlib.sha256(
            json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        ).hexdigest()

    def _request(self, **overrides: object) -> LearnedSkillRegistryRequest:
        values = {
            "owner": "owner_special",
            "record_fingerprint": self.record_fingerprint,
            "receipt_fingerprint": self.receipt["receipt_fingerprint"],
        }
        values.update(overrides)
        return LearnedSkillRegistryRequest(**values)

    def test_h10_receipt_materializes_learned_skill(self) -> None:
        skill = self.boundary.commit(self._request(), self.receipt, self.registry)
        self.assertEqual(skill.status, "approved")
        self.assertEqual(skill.name, "bounded-research")
        self.assertEqual(self.registry.names(), ("bounded-research",))

    def test_non_h10_authority_is_rejected(self) -> None:
        receipt = dict(self.receipt)
        receipt["promotion_authority"] = "H21"
        with self.assertRaises(LearnedSkillRegistryBoundaryError):
            self.boundary.commit(self._request(), receipt, self.registry)

    def test_unapproved_receipt_is_rejected(self) -> None:
        receipt = dict(self.receipt)
        receipt["approved"] = False
        with self.assertRaises(LearnedSkillRegistryBoundaryError):
            self.boundary.commit(self._request(), receipt, self.registry)

    def test_record_identity_is_bound(self) -> None:
        with self.assertRaises(LearnedSkillRegistryBoundaryError):
            self.boundary.commit(self._request(record_fingerprint="b" * 64), self.receipt, self.registry)

    def test_receipt_identity_is_bound(self) -> None:
        with self.assertRaises(LearnedSkillRegistryBoundaryError):
            self.boundary.commit(self._request(receipt_fingerprint="c" * 64), self.receipt, self.registry)

    def test_unsafe_candidate_is_rejected(self) -> None:
        receipt = dict(self.receipt)
        receipt["candidate"] = {"name": "bad", "goal": "execute subprocess", "procedure": ["run"]}
        with self.assertRaises(LearnedSkillRegistryBoundaryError):
            self.boundary.commit(self._request(), receipt, self.registry)

    def test_receipt_cannot_gain_authority(self) -> None:
        receipt = dict(self.receipt)
        receipt["authority"] = "H10"
        with self.assertRaises(LearnedSkillRegistryBoundaryError):
            self.boundary.commit(self._request(), receipt, self.registry)


if __name__ == "__main__":
    unittest.main()
