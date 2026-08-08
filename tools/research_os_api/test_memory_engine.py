import tempfile
import unittest
from pathlib import Path

from memory_engine import JsonMemoryStore, MemoryEngine


class MemoryEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = JsonMemoryStore(Path(self.temp.name) / "records.json")
        self.engine = MemoryEngine(self.store)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_remember_and_get(self) -> None:
        record = self.engine.remember(
            type="conversation",
            title="Provider choice",
            content="Use Gemini for this workspace",
            tags=["AI", "provider"],
            project_id="research-os",
            priority=5,
        )
        loaded = self.store.get(record.id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.content, "Use Gemini for this workspace")
        self.assertEqual(loaded.tags, ["ai", "provider"])

    def test_update_preserves_id_and_changes_timestamp(self) -> None:
        record = self.engine.remember(type="preference", content="dark mode")
        updated = self.store.update(record.id, content="system theme", tags=["ui"])
        self.assertEqual(updated.id, record.id)
        self.assertEqual(updated.content, "system theme")
        self.assertEqual(updated.tags, ["ui"])
        self.assertGreaterEqual(updated.updated_at, record.updated_at)

    def test_delete(self) -> None:
        record = self.engine.remember(type="knowledge", content="memory test")
        self.assertTrue(self.store.delete(record.id))
        self.assertFalse(self.store.delete(record.id))
        self.assertIsNone(self.store.get(record.id))

    def test_search_ranks_title_and_priority(self) -> None:
        first = self.engine.remember(
            type="knowledge",
            title="Memory Engine",
            content="Local-first storage design",
            priority=10,
        )
        self.engine.remember(
            type="knowledge",
            title="Other",
            content="Memory notes",
            priority=0,
        )
        hits = self.engine.search("memory", limit=10)
        self.assertEqual(hits[0].record.id, first.id)
        self.assertGreater(hits[0].score, hits[1].score)

    def test_search_filters_project_session_and_tags(self) -> None:
        wanted = self.engine.remember(
            type="conversation",
            content="Provider streaming decision",
            project_id="research-os",
            session_id="s1",
            tags=["provider", "stream"],
        )
        self.engine.remember(
            type="conversation",
            content="Provider streaming decision",
            project_id="other",
            session_id="s2",
            tags=["provider"],
        )
        hits = self.engine.search(
            "provider",
            project_id="research-os",
            session_id="s1",
            tags=["stream"],
        )
        self.assertEqual([hit.record.id for hit in hits], [wanted.id])

    def test_timeline_filters_session(self) -> None:
        first = self.engine.remember(type="conversation", content="first", session_id="s1")
        second = self.engine.remember(type="conversation", content="second", session_id="s2")
        timeline = self.engine.timeline(session_id="s1")
        self.assertEqual([item.id for item in timeline], [first.id])
        self.assertNotIn(second.id, [item.id for item in timeline])

    def test_rejects_empty_content(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.remember(type="conversation", content="   ")


if __name__ == "__main__":
    unittest.main()
