import os
import tempfile
import unittest
from pathlib import Path

import conversation_store


class ConversationStoreTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.previous_store = os.environ.get("RESEARCH_OS_CONVERSATION_STORE")
        self.previous_key = os.environ.get("RESEARCH_OS_SYNC_KEY")
        os.environ["RESEARCH_OS_CONVERSATION_STORE"] = str(
            Path(self.tempdir.name) / "conversations.json"
        )
        os.environ["RESEARCH_OS_SYNC_KEY"] = "test-sync-key"

    def tearDown(self):
        if self.previous_store is None:
            os.environ.pop("RESEARCH_OS_CONVERSATION_STORE", None)
        else:
            os.environ["RESEARCH_OS_CONVERSATION_STORE"] = self.previous_store
        if self.previous_key is None:
            os.environ.pop("RESEARCH_OS_SYNC_KEY", None)
        else:
            os.environ["RESEARCH_OS_SYNC_KEY"] = self.previous_key
        self.tempdir.cleanup()

    def test_sync_key_is_required(self):
        self.assertTrue(conversation_store.sync_configured())
        self.assertTrue(conversation_store.authorize("test-sync-key"))
        self.assertFalse(conversation_store.authorize("wrong"))
        self.assertFalse(conversation_store.authorize(None))

    def test_session_round_trip_and_delete(self):
        saved = conversation_store.upsert_session(
            {
                "id": "chat-1",
                "title": "Research OS",
                "updated_at": 123,
                "messages": [
                    {"role": "user", "text": "hello"},
                    {"role": "assistant", "text": "hi", "memory_count": 2},
                ],
            }
        )
        self.assertEqual("chat-1", saved["id"])
        sessions = conversation_store.list_sessions()
        self.assertEqual(1, len(sessions))
        self.assertEqual("Research OS", sessions[0]["title"])
        self.assertEqual(2, len(sessions[0]["messages"]))
        self.assertTrue(conversation_store.delete_session("chat-1"))
        self.assertEqual([], conversation_store.list_sessions())


if __name__ == "__main__":
    unittest.main()
