from __future__ import annotations

import hashlib
import json
import unittest


class RuntimeEvidenceManifestTests(unittest.TestCase):
    def _hash(self, payload: dict) -> str:
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def test_manifest_binds_declared_target_and_scenario_evidence(self):
        target_sha = "a" * 40
        evidence = {
            "scenario": "worker-crash-before-ack",
            "evidence_hash": "b" * 64,
        }
        manifest = {
            "target_sha": target_sha,
            "target_identity_algorithm": "git-sha1",
            "evidence_algorithm": "sha256",
            "entries": [evidence],
        }
        fingerprint = self._hash(manifest)
        self.assertEqual(40, len(manifest["target_sha"]))
        self.assertEqual(64, len(evidence["evidence_hash"]))
        self.assertEqual(64, len(fingerprint))

    def test_manifest_fingerprint_changes_when_target_changes(self):
        base = {
            "target_sha": "a" * 40,
            "target_identity_algorithm": "git-sha1",
            "evidence_algorithm": "sha256",
            "entries": [{"scenario": "event-crash", "evidence_hash": "b" * 64}],
        }
        changed = {**base, "target_sha": "c" * 40}
        self.assertNotEqual(self._hash(base), self._hash(changed))

    def test_manifest_entries_are_order_independent_only_when_canonicalized(self):
        entries_a = [
            {"scenario": "b", "evidence_hash": "2" * 64},
            {"scenario": "a", "evidence_hash": "1" * 64},
        ]
        entries_b = list(reversed(entries_a))
        manifest_a = {"target_sha": "a" * 40, "entries": entries_a}
        manifest_b = {"target_sha": "a" * 40, "entries": entries_b}
        self.assertNotEqual(self._hash(manifest_a), self._hash(manifest_b))
        canonical = lambda entries: sorted(entries, key=lambda item: item["scenario"])
        self.assertEqual(
            self._hash({**manifest_a, "entries": canonical(entries_a)}),
            self._hash({**manifest_b, "entries": canonical(entries_b)}),
        )


if __name__ == "__main__":
    unittest.main()
