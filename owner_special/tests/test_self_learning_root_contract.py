from __future__ import annotations

import unittest

from owner_special.research_os_friend.self_learning import LearnedSkillCandidate, SelfLearningEngine


class SelfLearningRootContractTests(unittest.TestCase):
    def test_high_confidence_candidate_without_evidence_cannot_be_promoted(self) -> None:
        engine = SelfLearningEngine()
        candidate = LearnedSkillCandidate(
            name="evidence-free-candidate",
            goal="looks plausible but has no verification evidence",
            procedure=("inspect", "validate"),
            evidence=(),
            confidence=0.99,
        )

        # Root contract: confidence alone is never sufficient for promotion.
        # This test intentionally targets the first self-learning implementation.
        self.assertIsNone(engine.learn(candidate))
        self.assertEqual(engine.registry.names(), ())


if __name__ == "__main__":
    unittest.main()
