#!/usr/bin/env python3
from __future__ import annotations

import unittest

from v2_brain_context import ContextEngine, ContextSource


class FakeMemory:
    def recall(self, query: str, *, limit: int = 8) -> list[dict[str, object]]:
        return [{"query": query, "limit": limit, "fact": "previous verified decision"}]


class BrainContextTests(unittest.TestCase):
    def test_higher_authority_wins_and_conflict_is_preserved(self) -> None:
        engine = ContextEngine()
        snapshot = engine.build(
            [
                ContextSource("memory", 50, {"branch": "old"}),
                ContextSource("project_state", 90, {"branch": "current"}, required=True),
            ]
        )
        self.assertEqual("current", snapshot.values["branch"])
        self.assertEqual(1, len(snapshot.conflicts))
        self.assertEqual("project_state", snapshot.conflicts[0].selected_source)
        self.assertEqual("memory", snapshot.conflicts[0].rejected_source)

    def test_context_redacts_sensitive_keys_before_snapshot(self) -> None:
        snapshot = ContextEngine().build(
            [ContextSource("provider", 70, {"api_key": "never-leak", "state": "ready"})]
        )
        self.assertEqual("[REDACTED]", snapshot.values["api_key"])
        self.assertEqual("ready", snapshot.values["state"])
        self.assertNotIn("never-leak", repr(snapshot))

    def test_budget_drops_optional_values_but_keeps_required_source(self) -> None:
        engine = ContextEngine(default_budget_chars=1000)
        snapshot = engine.build(
            [
                ContextSource("system", 100, {"identity": "Research OS"}, required=True),
                ContextSource("optional", 10, {"large": "x" * 5000}),
            ]
        )
        self.assertEqual("Research OS", snapshot.values["identity"])
        self.assertNotIn("large", snapshot.values)
        self.assertIn("large", snapshot.dropped_keys)

    def test_memory_recall_is_added_as_context_source(self) -> None:
        engine = ContextEngine(memory=FakeMemory())
        snapshot = engine.build(
            [ContextSource("user", 90, {"objective": "debug CI"}, required=True)],
            objective="debug CI",
        )
        self.assertIn("memory_recall", snapshot.values)
        self.assertEqual("previous verified decision", snapshot.values["memory_recall"][0]["fact"])
        source_names = {item["name"] for item in snapshot.sources}
        self.assertIn("long_term_memory", source_names)

    def test_tied_authority_is_deterministic_by_source_name(self) -> None:
        snapshot = ContextEngine().build(
            [
                ContextSource("z-source", 50, {"value": "z"}),
                ContextSource("a-source", 50, {"value": "a"}),
            ]
        )
        self.assertEqual("a", snapshot.values["value"])
        self.assertEqual("a-source", snapshot.conflicts[0].selected_source)


if __name__ == "__main__":
    unittest.main()
