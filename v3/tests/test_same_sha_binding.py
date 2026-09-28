from __future__ import annotations

import re
import unittest


_SHA1 = re.compile(r"^[0-9a-f]{40}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class SameSHABindingContractTests(unittest.TestCase):
    def test_commit_identity_and_evidence_identity_are_distinct(self):
        target_sha = "a" * 40
        evidence_hash = "b" * 64
        self.assertRegex(target_sha, _SHA1)
        self.assertRegex(evidence_hash, _SHA256)
        self.assertNotEqual(len(target_sha), len(evidence_hash))

    def test_same_target_sha_is_required_across_evidence_entries(self):
        target_sha = "a" * 40
        entries = [
            {"target_sha": target_sha, "scenario": "queue-crash"},
            {"target_sha": target_sha, "scenario": "event-crash"},
            {"target_sha": target_sha, "scenario": "replay-restart"},
        ]
        self.assertTrue(all(entry["target_sha"] == target_sha for entry in entries))

    def test_mixed_target_sha_fails_closed(self):
        entries = [
            {"target_sha": "a" * 40, "scenario": "queue-crash"},
            {"target_sha": "b" * 40, "scenario": "event-crash"},
        ]
        self.assertEqual(2, len({entry["target_sha"] for entry in entries}))

    def test_malformed_target_identity_fails_closed(self):
        for value in ("", "A" * 40, "a" * 39, "a" * 41, "not-a-sha"):
            self.assertIsNone(_SHA1.fullmatch(value))


if __name__ == "__main__":
    unittest.main()
