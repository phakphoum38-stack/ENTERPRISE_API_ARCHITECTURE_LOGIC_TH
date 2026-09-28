import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tools.aeos_autobot_evidence_manifest import SnapshotLock, build_manifest, evidence_id, verify_manifest, write_manifest
from tools.aeos_autobot_state_machine import Evidence, ResultState, Snapshot


class TestAutobotEvidenceManifest(unittest.TestCase):
    def lock(self, source_sha="a" * 40, sets=("S01", "S02")):
        return SnapshotLock("iteration-1", source_sha, "batch-1", "run-1", tuple(sets), "2026-09-11T00:00:00Z", "2026-09-11T00:00:01Z")

    def evidence(self, set_id, state=ResultState.PASSED, source_sha="a" * 40, iteration="iteration-1"):
        snap = Snapshot(iteration, source_sha, set_id, "W0", "python -m unittest", ".")
        return Evidence(snap, state, evidence_id(snap, state))

    def test_manifest_is_deterministic(self):
        lock = self.lock()
        items = [self.evidence("S02"), self.evidence("S01")]
        first = build_manifest(lock, "W0", items, ResultState.PASSED)
        second = build_manifest(lock, "W0", reversed(items), ResultState.PASSED)
        self.assertEqual(first, second)
        self.assertEqual(first["manifest_sha256"], hashlib.sha256((json.dumps({**first, "manifest_sha256": ""}, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()).hexdigest())

    def test_wrong_source_sha_is_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest(self.lock(), "W0", [self.evidence("S01", source_sha="b" * 40), self.evidence("S02")], ResultState.PASSED)

    def test_wrong_iteration_is_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest(self.lock(), "W0", [self.evidence("S01", iteration="iteration-old"), self.evidence("S02")], ResultState.PASSED)

    def test_duplicate_set_is_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest(self.lock(), "W0", [self.evidence("S01"), self.evidence("S01")], ResultState.PASSED)

    def test_incomplete_set_is_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest(self.lock(), "W0", [self.evidence("S01")], ResultState.PASSED)

    def test_running_evidence_is_rejected(self):
        with self.assertRaises(ValueError):
            build_manifest(self.lock(), "W0", [self.evidence("S01", ResultState.RUNNING), self.evidence("S02")], ResultState.HOLD)

    def test_failed_evidence_cannot_claim_pass(self):
        with self.assertRaises(ValueError):
            build_manifest(self.lock(), "W0", [self.evidence("S01", ResultState.FAILED), self.evidence("S02")], ResultState.PASSED)

    def test_written_manifest_and_sidecar_verify(self):
        lock = self.lock()
        manifest = build_manifest(lock, "W0", [self.evidence("S01"), self.evidence("S02")], ResultState.PASSED)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "evidence.json"
            write_manifest(manifest, path)
            verify_manifest(path)
            path.write_text(path.read_text(encoding="utf-8").replace("\"decision\":\"PASSED\"", "\"decision\":\"HOLD\""), encoding="utf-8")
            with self.assertRaises(ValueError):
                verify_manifest(path)


if __name__ == "__main__":
    unittest.main()
