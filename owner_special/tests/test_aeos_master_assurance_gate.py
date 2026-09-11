import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.aeos_master_assurance_gate import run_gate


class TestMasterAssuranceGate(unittest.TestCase):
    def _manifest(self, root: Path, *, source_sha: str = "a" * 40, iteration_id: str = "iteration-1") -> Path:
        payload = {
            "schema_version": "1.0",
            "platform": "AEOS_AUTOBOT_PLATFORM",
            "iteration_id": iteration_id,
            "source_sha": source_sha,
            "decision": "READY_FOR_OWNER_AUTHORITY",
            "authority": "OWNER_ONLY",
            "results": [{
                "set_id": "SET-001",
                "name": "test",
                "wave": "IDENTITY",
                "state": "PASSED",
                "returncode": 0,
                "command": "true",
                "cwd": str(root),
                "duration_seconds": 0.1,
                "source_sha": source_sha,
                "iteration_id": iteration_id,
                "evidence_id": "b" * 64,
                "detail": "pass",
            }],
        }
        path = root / "execution.json"
        raw = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
        path.write_bytes(raw)
        path.with_suffix(path.suffix + ".sha256").write_text(
            hashlib.sha256(raw).hexdigest() + "  " + path.name + "\n", encoding="utf-8"
        )
        return path

    def test_missing_assurance_proof_is_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._manifest(root)
            proof = root / "missing-proof.json"
            output = root / "composition.json"
            with patch("tools.aeos_master_assurance_gate.load_proof", side_effect=FileNotFoundError("missing")):
                self.assertEqual(run_gate(manifest, proof, output), 2)
            self.assertFalse(output.exists())

    def test_execution_identity_mismatch_is_hold(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._manifest(root)
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["results"][0]["source_sha"] = "c" * 40
            raw = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            manifest.write_bytes(raw)
            manifest.with_suffix(manifest.suffix + ".sha256").write_text(
                hashlib.sha256(raw).hexdigest() + "  " + manifest.name + "\n", encoding="utf-8"
            )
            with self.assertRaises(ValueError):
                run_gate(manifest, root / "proof.json", root / "composition.json")

    def test_manifest_integrity_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = self._manifest(root)
            sidecar = manifest.with_suffix(manifest.suffix + ".sha256")
            sidecar.write_text("0" * 64 + "  execution.json\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                run_gate(manifest, root / "proof.json", root / "composition.json")


if __name__ == "__main__":
    unittest.main()
