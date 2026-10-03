from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import qr_pairing


class QRPairingTests(unittest.TestCase):
    def setUp(self):
        self.data = tempfile.TemporaryDirectory()
        self.prev = os.environ.get("RESEARCH_OS_DATA_DIR")
        os.environ["RESEARCH_OS_DATA_DIR"] = self.data.name

    def tearDown(self):
        if self.prev is None:
            os.environ.pop("RESEARCH_OS_DATA_DIR", None)
        else:
            os.environ["RESEARCH_OS_DATA_DIR"] = self.prev
        self.data.cleanup()

    def test_secret_is_hashed_at_rest(self):
        created = qr_pairing.create_pairing()
        raw = Path(self.data.name, "qr_pairings.json").read_text(encoding="utf-8")
        self.assertNotIn(created["pairing_secret"], raw)
        self.assertEqual(qr_pairing.get_status(created["pairing_id"], created["pairing_secret"])["status"], "PENDING")

    def test_invalid_secret_fails_closed(self):
        created = qr_pairing.create_pairing()
        with self.assertRaises(qr_pairing.QRPairingError):
            qr_pairing.get_status(created["pairing_id"], "wrong")

    def test_oauth_binding_is_single_use(self):
        created = qr_pairing.create_pairing()
        qr_pairing.bind_oauth_state(created["pairing_id"], created["pairing_secret"], "oauth-state", "github")
        binding = qr_pairing.consume_oauth_binding("oauth-state")
        self.assertEqual(binding["pairing_id"], created["pairing_id"])
        self.assertEqual(binding["pairing_secret"], created["pairing_secret"])
        self.assertIsNone(qr_pairing.consume_oauth_binding("oauth-state"))

    def test_completed_pairing_never_persists_session(self):
        created = qr_pairing.create_pairing()
        qr_pairing.complete_pairing(
            created["pairing_id"],
            provider="github",
            account={"user_id": "github:123", "email": "owner@example.com", "role": "OWNER", "session": "SECRET"},
        )
        raw = Path(self.data.name, "qr_pairings.json").read_text(encoding="utf-8")
        self.assertNotIn("SECRET", raw)
        self.assertTrue(qr_pairing.get_status(created["pairing_id"], created["pairing_secret"])["connected"])


if __name__ == "__main__":
    unittest.main()
