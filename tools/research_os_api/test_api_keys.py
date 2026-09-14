import os
import unittest
from datetime import datetime, timedelta, timezone

from api_key_store import InMemoryAPIKeyStore
from api_keys import APIKeyManager


class APIKeyManagerTests(unittest.TestCase):
    def setUp(self):
        os.environ["RESEARCH_OS_API_KEY_PEPPER"] = "test-pepper"

    def test_manager_uses_injected_canonical_store(self):
        store = InMemoryAPIKeyStore()
        manager = APIKeyManager(store)
        record, raw = manager.create("user-1", {"agent:run"})
        self.assertIsNotNone(store.get(record.key_id))
        self.assertEqual(manager.verify(raw, required_scope="agent:run").key_id, record.key_id)

    def test_scope_expiry_and_revoke_are_enforced(self):
        store = InMemoryAPIKeyStore()
        manager = APIKeyManager(store)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)
        record, raw = manager.create("user-1", {"agent:run"}, expires_at=expires_at)
        self.assertIsNone(manager.verify(raw, required_scope="admin"))
        self.assertIsNotNone(manager.verify(raw, required_scope="agent:run"))
        manager.revoke(record.key_id)
        self.assertIsNone(manager.verify(raw))

    def test_unknown_and_invalid_keys_fail_closed(self):
        manager = APIKeyManager(InMemoryAPIKeyStore())
        self.assertIsNone(manager.verify("invalid"))
        with self.assertRaises(ValueError):
            manager.revoke("missing")


if __name__ == "__main__":
    unittest.main()
