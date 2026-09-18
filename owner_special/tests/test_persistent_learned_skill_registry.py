from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from owner_special.research_os_friend.self_learning import (
    LearnedSkillCandidate,
    LearnedSkillRegistry,
    PersistentLearnedSkillRegistry,
)


class PersistentLearnedSkillRegistryTests(unittest.TestCase):
    def candidate(self) -> LearnedSkillCandidate:
        return LearnedSkillCandidate(
            name="bounded-research",
            goal="reuse a verified research procedure",
            procedure=("inspect evidence", "validate result"),
            evidence=("EV-001",),
            confidence=0.95,
            status="candidate",
            version=1,
        )

    def test_save_and_load_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learned.json"
            source = LearnedSkillRegistry()
            approved = source.promote(self.candidate())
            PersistentLearnedSkillRegistry(path, source).save()

            restored = LearnedSkillRegistry()
            loaded = PersistentLearnedSkillRegistry(path, restored).load()

            self.assertEqual(loaded, (approved,))
            self.assertEqual(restored.get("bounded-research"), approved)

    def test_save_is_atomic_and_json_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learned.json"
            registry = LearnedSkillRegistry()
            registry.promote(self.candidate())
            store = PersistentLearnedSkillRegistry(path, registry)
            store.save()
            first = path.read_text(encoding="utf-8")
            store.save()
            self.assertEqual(first, path.read_text(encoding="utf-8"))
            self.assertEqual(json.loads(first)["format_version"], 1)

    def test_missing_file_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loaded = PersistentLearnedSkillRegistry(Path(tmp) / "missing.json").load()
            self.assertEqual(loaded, ())

    def test_unapproved_record_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learned.json"
            path.write_text(
                json.dumps({"format_version": 1, "skills": [{"name": "x", "status": "candidate"}]}),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                PersistentLearnedSkillRegistry(path).load()


if __name__ == "__main__":
    unittest.main()
