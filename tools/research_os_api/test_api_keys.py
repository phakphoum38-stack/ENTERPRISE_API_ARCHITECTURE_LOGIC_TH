import os
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

from api_keys import APIKeyError, APIKeyManager
from entitlements import EntitlementRegistry, PrincipalBinding
from resource_governance import Entitlement


NOW = datetime(2026, 9, 14, 15, 0, tzinfo=timezone.utc)


class APIKeyLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pepper = mock.patch.dict(os.environ, {"RESEARCH_OS_API_KEY_PEPPER": "test-pepper"})
        self.pepper.start()
        self.addCleanup(self.pepper.stop)

    def test_create_and_verify_never_exposes_digest(self) -> None:
        manager = APIKeyManager()
        record, raw = manager.create("user-1", frozenset({"chat"}))
        self.assertTrue(raw.startswith(manager.PREFIX))
        self.assertEqual(manager.verify(raw, required_scope="chat", now=NOW), record)
        self.assertNotIn(raw, manager._digests.values())

    def test_required_scope_is_fail_closed_when_blank(self) -> None:
        manager = APIKeyManager()
        _, raw = manager.create("user-1", frozenset({"chat"}))
        self.assertIsNone(manager.verify(raw, required_scope="   ", now=NOW))

    def test_key_scopes_cannot_exceed_entitlement(self) -> None:
        registry = EntitlementRegistry()
        registry.bind(PrincipalBinding("user-1", Entitlement(tier="developer", scopes=frozenset({"chat"}))), now=NOW)
        manager = APIKeyManager(entitlements=registry)
        with self.assertRaisesRegex(APIKeyError, "exceed principal entitlement"):
            manager.create("user-1", frozenset({"chat", "admin"}))
        record, _ = manager.create("user-1", frozenset({"chat"}))
        self.assertEqual(record.scopes, frozenset({"chat"}))

    def test_rotate_revokes_old_key_and_issues_new_key(self) -> None:
        manager = APIKeyManager()
        old_record, old_raw = manager.create("user-1", frozenset({"chat"}), expires_at=datetime.now(timezone.utc) + timedelta(days=1))
        new_record, new_raw = manager.rotate(old_record.key_id, expires_at=datetime.now(timezone.utc) + timedelta(days=2), now=datetime.now(timezone.utc))
        self.assertNotEqual(old_record.key_id, new_record.key_id)
        self.assertIsNone(manager.verify(old_raw, now=NOW))
        self.assertEqual(manager.verify(new_raw, required_scope="chat", now=NOW), new_record)
        self.assertTrue(manager.list("user-1")[0].revoked_at is not None)

    def test_rotate_rejects_expired_key(self) -> None:
        manager = APIKeyManager()
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=1)
        record, _ = manager.create("user-1", frozenset({"chat"}), expires_at=expires_at)
        with self.assertRaisesRegex(APIKeyError, "inactive"):
            manager.rotate(record.key_id, now=expires_at + timedelta(seconds=1))


if __name__ == "__main__":
    unittest.main()
