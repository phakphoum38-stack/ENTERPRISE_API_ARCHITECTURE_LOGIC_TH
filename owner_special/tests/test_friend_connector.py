from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.research_os_api.friend_connector import (
    ConnectionProfileStore,
    FriendConnectionProfile,
    FriendConnector,
    MemoryConnectionCredentialStore,
)


class FriendConnectorProfileTests(unittest.TestCase):
    def test_profile_rejects_non_owner_scope(self):
        with self.assertRaises(ValueError):
            FriendConnectionProfile("x", "X", "owner", owner_scope="shared")

    def test_profile_round_trip(self):
        with tempfile.TemporaryDirectory() as root:
            store = ConnectionProfileStore(Path(root), "owner")
            profile = FriendConnectionProfile("iphone", "My iPhone", "owner", transport="http")
            store.upsert(profile)
            self.assertEqual(store.get("iphone"), profile)

    def test_profile_password_is_not_serialized(self):
        profile = FriendConnectionProfile("iphone", "My iPhone", "owner")
        self.assertNotIn("password", profile.public_dict())

    def test_auto_prefers_direct_and_falls_back(self):
        with tempfile.TemporaryDirectory() as root:
            connector = FriendConnector(owner_id="owner", data_root=Path(root), credential_store=MemoryConnectionCredentialStore())
            connector.profiles.upsert(FriendConnectionProfile("auto", "Auto", "owner", transport="auto"))
            with patch.object(connector, "_direct_chat", side_effect=RuntimeError("direct down")) as direct:
                with patch.object(connector, "_http_request", return_value={"text": "ok"}) as http:
                    result = connector.chat("auto", {"text": "hello"})
            direct.assert_called_once()
            http.assert_called_once()
            self.assertEqual(result["transport"], "http")
            self.assertTrue(result["fallback_used"])

    def test_locked_profile_does_not_failover(self):
        with tempfile.TemporaryDirectory() as root:
            connector = FriendConnector(owner_id="owner", data_root=Path(root))
            connector.profiles.upsert(FriendConnectionProfile("locked", "Locked", "owner", transport="auto", locked=True))
            with patch.object(connector, "_direct_chat", side_effect=RuntimeError("direct down")) as direct:
                with patch.object(connector, "_http_request") as http:
                    with self.assertRaises(Exception):
                        connector.chat("locked", {"text": "hello"})
            direct.assert_called_once()
            http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
