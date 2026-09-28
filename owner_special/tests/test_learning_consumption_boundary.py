import unittest

from owner_special.research_os_friend.learning_registry_integrity import LearningRegistry, LearningRegistryEntry
from owner_special.research_os_friend.learning_consumption_boundary import LearningConsumptionError, LearningConsumptionRequest, LearningSkillConsumer


class LearningConsumptionBoundaryTests(unittest.TestCase):
    def _entry(self, **overrides):
        values = {
            "owner": "owner-special",
            "source_sha": "a" * 40,
            "correlation_id": "corr-001",
            "name": "safe-search",
            "goal": "find bounded documentation",
            "evidence_fingerprint": "b" * 64,
            "promotion_fingerprint": "c" * 64,
        }
        values.update(overrides)
        return LearningRegistryEntry(**values)

    def test_inspection_is_allowed_for_exact_identity(self):
        registry = LearningRegistry()
        entry = self._entry()
        registry.add(entry)
        request = LearningConsumptionRequest("owner-special", "a" * 40, "corr-001", entry.fingerprint)
        result = LearningSkillConsumer(registry).inspect(request)
        self.assertEqual(result["decision"], "ALLOW_INSPECTION")
        self.assertTrue(result["read_only"])
        self.assertEqual(result["authority"], "none")

    def test_execution_intent_requires_approval(self):
        registry = LearningRegistry()
        entry = self._entry()
        registry.add(entry)
        request = LearningConsumptionRequest("owner-special", "a" * 40, "corr-001", entry.fingerprint, "execute")
        result = LearningSkillConsumer(registry).decide(request)
        self.assertEqual(result["decision"], "REQUIRE_APPROVAL")
        self.assertTrue(result["read_only"])

    def test_identity_mismatch_fails_closed(self):
        registry = LearningRegistry()
        entry = self._entry()
        registry.add(entry)
        request = LearningConsumptionRequest("other-owner", "a" * 40, "corr-001", entry.fingerprint)
        with self.assertRaises(LearningConsumptionError):
            LearningSkillConsumer(registry).inspect(request)

    def test_missing_skill_fails_closed(self):
        registry = LearningRegistry()
        request = LearningConsumptionRequest("owner-special", "a" * 40, "corr-001", "d" * 64)
        with self.assertRaises(LearningConsumptionError):
            LearningSkillConsumer(registry).inspect(request)

    def test_snapshot_is_defensively_copied(self):
        registry = LearningRegistry()
        entry = self._entry()
        registry.add(entry)
        request = LearningConsumptionRequest("owner-special", "a" * 40, "corr-001", entry.fingerprint)
        result = LearningSkillConsumer(registry).inspect(request)
        result["skill"]["name"] = "mutated"
        self.assertEqual(LearningSkillConsumer(registry).inspect(request)["skill"]["name"], "safe-search")

    def test_invalid_intent_is_rejected(self):
        with self.assertRaises(LearningConsumptionError):
            LearningConsumptionRequest("owner-special", "a" * 40, "corr-001", "d" * 64, "run")

    def test_decision_is_deterministic(self):
        registry = LearningRegistry()
        entry = self._entry()
        registry.add(entry)
        request = LearningConsumptionRequest("owner-special", "a" * 40, "corr-001", entry.fingerprint)
        consumer = LearningSkillConsumer(registry)
        self.assertEqual(consumer.inspect(request)["decision_fingerprint"], consumer.inspect(request)["decision_fingerprint"])


if __name__ == "__main__":
    unittest.main()
