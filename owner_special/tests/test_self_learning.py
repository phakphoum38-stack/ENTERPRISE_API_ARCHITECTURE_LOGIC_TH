from __future__ import annotations

import unittest

from owner_special.research_os_friend.models import FriendRequest
from owner_special.research_os_friend.runtime import FriendRuntime
from owner_special.research_os_friend.self_learning import LearnedSkillCandidate, LearnedSkillRegistry, SelfLearningEngine


class SelfLearningTests(unittest.TestCase):
    def test_candidate_requires_validation_before_promotion(self):
        engine = SelfLearningEngine()
        candidate = engine.propose(
            name="learned-review",
            goal="Review a repeated repository task",
            procedure=("inspect evidence", "run validation", "record result"),
            evidence=("test-pass", "reviewed-diff"),
            confidence=0.95,
        )
        approved = engine.learn(candidate)
        self.assertIsNotNone(approved)
        self.assertEqual(approved.status, "approved")
        self.assertEqual(engine.registry.names(), ("learned-review",))

    def test_low_confidence_candidate_is_not_promoted(self):
        engine = SelfLearningEngine()
        candidate = LearnedSkillCandidate(
            name="unsafe-shortcut",
            goal="guess a solution",
            procedure=("guess",),
            evidence=(),
            confidence=0.2,
        )
        self.assertIsNone(engine.learn(candidate))
        self.assertEqual(engine.registry.names(), ())

    def test_runtime_exposes_self_learning_without_mutating_core_skills(self):
        runtime = FriendRuntime.create_owner_special("phakphum")
        core_before = runtime.orchestrator.skills.names()
        approved = runtime.learn_skill(
            name="learned-repo-review",
            goal="Repeat a verified repository review",
            procedure=("inspect", "validate", "record evidence"),
            evidence=("review-pass", "test-pass"),
            confidence=0.95,
        )
        self.assertIsNotNone(approved)
        self.assertIn("self_learning", core_before)
        self.assertEqual(runtime.orchestrator.skills.names(), core_before)
        snapshot = runtime.self_learning_snapshot()
        self.assertTrue(snapshot["approval_required"])
        self.assertFalse(snapshot["core_mutation"])
        self.assertEqual(snapshot["approved_skills"][0]["name"], "learned-repo-review")

    def test_self_learning_skill_is_routable(self):
        runtime = FriendRuntime.create_owner_special("phakphum")
        response = runtime.ask(
            FriendRequest(
                owner_id="phakphum",
                text="propose a validated reusable skill from evidence",
                requested_skills=("self_learning",),
            )
        )
        self.assertEqual(response.decision.selected_skills, ("self_learning",))


if __name__ == "__main__":
    unittest.main()
