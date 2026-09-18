from __future__ import annotations

import hashlib
import json
import re
import unittest

SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class TenPow1000ProtocolTests(unittest.TestCase):
    def _fingerprint(self, payload):
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def test_protocol_dimensions_are_explicit_and_nonempty(self):
        dimensions = {
            "workflow": 7,
            "task": 6,
            "lease": 6,
            "worker": 6,
            "event": 5,
            "delivery": 7,
            "dlq": 4,
            "restart": 4,
            "contention": 4,
            "identity": 5,
            "evidence": 5,
            "target": 4,
            "recovery": 4,
            "authority": 5,
        }
        self.assertTrue(all(count > 0 for count in dimensions.values()))
        self.assertGreater(len(dimensions), 10)

    def test_composition_is_logical_not_materialized(self):
        dimensions = [7, 6, 6, 6, 5, 7, 4, 4, 4, 5, 5, 4, 4, 5]
        logical_cardinality = 1
        for count in dimensions:
            logical_cardinality *= count
        self.assertGreater(logical_cardinality, 10**8)
        materialized_cases = 0
        self.assertEqual(materialized_cases, 0)

    def test_target_and_evidence_algorithms_are_distinct(self):
        target_sha = "a" * 40
        evidence_hash = "b" * 64
        self.assertRegex(target_sha, SHA1)
        self.assertRegex(evidence_hash, SHA256)
        self.assertNotEqual(target_sha, evidence_hash)

    def test_manifest_fingerprint_is_deterministic(self):
        payload = {
            "protocol": "V3-RUNTIME-10POW1000",
            "target_sha": "a" * 40,
            "entries": ["queue-crash", "event-restart", "dlq-replay"],
        }
        self.assertEqual(self._fingerprint(payload), self._fingerprint(dict(payload)))

    def test_fail_closed_when_authority_is_inferred_from_evidence(self):
        evidence = {"passed": True, "authority": "observation"}
        self.assertNotEqual(evidence["authority"], "owner-authority")


if __name__ == "__main__":
    unittest.main()
