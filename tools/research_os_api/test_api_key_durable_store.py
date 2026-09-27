import os
import tempfile
import unittest
from datetime import datetime, timezone

from tools.research_os_api.api_key_store import JsonAPIKeyStore
from tools.research_os_api.api_keys import APIKeyManager


class DurableAPIKeyTests(unittest.TestCase):
    def test_create_verify_rotate_and_revoke_without_plaintext_persistence(self):
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, "keys.json")
            manager = APIKeyManager(JsonAPIKeyStore(path))
            first, raw = manager.create("principal-1", {"scope:read"})
            self.assertIsNotNone(manager.verify(raw))
            second, replacement = manager.rotate(first.key_id, "principal-1", {"scope:read"})
            self.assertIsNone(manager.verify(raw))
            self.assertIsNotNone(manager.verify(replacement))
            text = open(path, encoding="utf-8").read()
            self.assertNotIn(raw, text)
            self.assertNotIn(replacement, text)
            manager.revoke(second.key_id)
            self.assertIsNone(manager.verify(replacement))


if __name__ == "__main__":
    unittest.main()
