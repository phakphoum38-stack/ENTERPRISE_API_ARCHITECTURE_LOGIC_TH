import unittest

from owner_special.research_os_friend.learning_registry_integrity import (
    LearningRegistry,
    LearningRegistryEntry,
    LearningRegistryError,
)


class LearningRegistryIntegrityTests(unittest.TestCase):
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

    def test_valid_entry_has_deterministic_fingerprint(self):
        first = self._entry()
        second = self._entry()
        self.assertEqual(first.fingerprint, second.fingerprint)

    def test_registry_snapshot_is_bounded_and_read_only(self):
        registry = LearningRegistry()
        registry.add(self._entry())
        snapshot = registry.snapshot()
        self.assertTrue(snapshot["read_only"])
        self.assertEqual(snapshot["authority"], "none")
        self.assertEqual(len(snapshot["entries"]), 1)
        snapshot["entries"][0]["name"] = "mutated"
        self.assertEqual(registry.snapshot()["entries"][0]["name"], "safe-search")

    def test_duplicate_entry_is_idempotent(self):
        registry = LearningRegistry()
        entry = self._entry()
        self.assertIs(registry.add(entry), entry)
        self.assertIs(registry.add(entry), entry)
        self.assertEqual(len(registry.snapshot()["entries"]), 1)

    def test_conflicting_version_is_rejected(self):
        registry = LearningRegistry()
        registry.add(self._entry())
        with self.assertRaises(LearningRegistryError):
            registry.add(self._entry(promotion_fingerprint="d" * 64))

    def test_secret_like_name_is_rejected(self):
        with self.assertRaises(LearningRegistryError):
            self._entry(name="api_key_rotation")

    def test_invalid_sha_is_rejected(self):
        with self.assertRaises(LearningRegistryError):
            self._entry(source_sha="not-a-sha")

    def test_registry_order_is_deterministic(self):
        registry = LearningRegistry()
        registry.add(self._entry(name="zeta"))
        registry.add(self._entry(name="alpha", promotion_fingerprint="d" * 64))
        names = [item["name"] for item in registry.snapshot()["entries"]]
        self.assertEqual(names, ["alpha", "zeta"])


if __name__ == "__main__":
    unittest.main()
