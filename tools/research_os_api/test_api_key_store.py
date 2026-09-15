import unittest
from datetime import datetime, timezone

from api_key_store import InMemoryAPIKeyStore, StoredAPIKey


class APIKeyStoreTests(unittest.TestCase):
    def _record(self, key_id="key_1", principal_id="user-1", digest="digest-1"):
        return StoredAPIKey(
            key_id=key_id,
            principal_id=principal_id,
            fingerprint="fingerprint",
            digest=digest,
            scopes=frozenset({"agent:run"}),
            created_at=datetime(2026, 9, 14, tzinfo=timezone.utc),
            expires_at=None,
        )

    def test_put_get_and_find_by_digest(self):
        store = InMemoryAPIKeyStore()
        record = self._record()
        store.put(record)
        self.assertEqual(store.get(record.key_id), record)
        self.assertEqual(store.find_by_digest(record.digest), record)

    def test_list_can_be_scoped_to_principal(self):
        store = InMemoryAPIKeyStore()
        store.put(self._record())
        store.put(self._record("key_2", "user-2", "digest-2"))
        self.assertEqual([item.key_id for item in store.list("user-1")], ["key_1"])
        self.assertEqual(len(store.list()), 2)

    def test_revoke_is_idempotent_and_persistent(self):
        store = InMemoryAPIKeyStore()
        record = self._record()
        store.put(record)
        revoked_at = datetime(2026, 9, 15, tzinfo=timezone.utc)
        revoked = store.revoke(record.key_id, revoked_at)
        self.assertEqual(revoked.revoked_at, revoked_at)
        self.assertEqual(store.revoke(record.key_id, revoked_at), revoked)

    def test_revoke_unknown_key_fails_closed(self):
        with self.assertRaises(KeyError):
            InMemoryAPIKeyStore().revoke("missing", datetime.now(timezone.utc))


if __name__ == "__main__":
    unittest.main()
