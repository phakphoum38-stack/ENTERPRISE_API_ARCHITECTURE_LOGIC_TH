import json
import tempfile
import unittest
from pathlib import Path

from tools.validate_aeos_final_gate_binding import validate_manifest


SHA = "a" * 40


def manifest(source_sha=SHA, decision="PASS", status="PASS", returncode=0):
    return {
        "schema": "AEOS_MASTER_ASSURANCE_V2",
        "source_sha": source_sha,
        "decision": decision,
        "control_count": 1,
        "controls": [{
            "control_id": "IDENTITY_SHA",
            "status": status,
            "returncode": returncode,
            "evidence_id": "b" * 64,
        }],
    }


class AEOFinalGateBindingTests(unittest.TestCase):
    def write(self, payload):
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False)
        with handle:
            json.dump(payload, handle)
        return Path(handle.name)

    def test_accepts_exact_sha_and_all_pass(self):
        path = self.write(manifest())
        try:
            result = validate_manifest(path, SHA)
            self.assertEqual(result["binding"], "PASS")
        finally:
            path.unlink()

    def test_rejects_sha_mismatch(self):
        path = self.write(manifest(source_sha="c" * 40))
        try:
            with self.assertRaises(ValueError):
                validate_manifest(path, SHA)
        finally:
            path.unlink()

    def test_rejects_non_pass_decision(self):
        path = self.write(manifest(decision="FAIL", status="FAIL", returncode=1))
        try:
            with self.assertRaises(ValueError):
                validate_manifest(path, SHA)
        finally:
            path.unlink()

    def test_rejects_unknown_control(self):
        path = self.write(manifest(status="UNKNOWN", returncode=1))
        try:
            with self.assertRaises(ValueError):
                validate_manifest(path, SHA)
        finally:
            path.unlink()


if __name__ == "__main__":
    unittest.main()
