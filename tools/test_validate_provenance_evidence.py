from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_provenance_evidence.py"
PRODUCER = ROOT / "tools" / "record_provenance_entry.py"
FIXTURE = ROOT / "current" / "PROVENANCE_EVIDENCE_LEDGER_FIXTURE.json"
CONTRACT = ROOT / "current" / "PROVENANCE_EVIDENCE_CONTRACT.json"

class ProvenanceEvidenceTests(unittest.TestCase):
    def load(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def validate(self, ledger):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as f:
            json.dump(ledger, f); path = Path(f.name)
        try:
            return subprocess.run([sys.executable, str(VALIDATOR), "--contract", str(CONTRACT), "--ledger", str(path)], cwd=ROOT, capture_output=True, text=True, check=False)
        finally:
            path.unlink(missing_ok=True)

    def test_canonical_fixture_passes(self):
        result = subprocess.run([sys.executable, str(VALIDATOR)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_payload_or_evidence_tamper_breaks_entry_hash(self):
        ledger = self.load(); ledger["entries"][0]["evidence"]["reason"] = "tampered"
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("entry_hash_mismatch:EV-001", json.loads(result.stdout)["errors"])

    def test_chain_tamper_breaks_previous_hash(self):
        ledger = self.load(); ledger["entries"][1]["previous_entry_hash"] = "0" * 64
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("previous_hash_mismatch:EV-002", json.loads(result.stdout)["errors"])

    def test_sequence_gap_fails_closed(self):
        ledger = self.load(); ledger["entries"][1]["sequence"] = 3
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_sequence:EV-002", json.loads(result.stdout)["errors"])

    def test_duplicate_entry_id_fails_closed(self):
        ledger = self.load(); ledger["entries"].append(copy.deepcopy(ledger["entries"][0]))
        ledger["entries"][-1]["sequence"] = 3
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate_entry_id:EV-001", json.loads(result.stdout)["errors"])

    def test_unknown_evidence_reference_fails_closed(self):
        ledger = self.load(); ledger["entries"][0]["evidence"]["evidence_ids"] = ["EV-999"]
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown_evidence_reference:EV-001", json.loads(result.stdout)["errors"])

    def test_producer_appends_and_verifies(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d); ledger = d / "ledger.json"; entry = d / "entry.json"
            ledger.write_text(json.dumps({"contract_version":"1.0.0","entries":[]}), encoding="utf-8")
            entry.write_text(json.dumps({"entry_id":"EV-PRODUCER","recorded_at":"2026-09-09T00:00:00Z","actor_id":"H-OWNER","action":"test","subject_type":"test","subject_id":"T-001","input_hashes":{"source":"47f18e77cad4716870add0689757110de4df276741299c2f0efec4d97a298aef"},"output_hashes":{"result":"47f18e77cad4716870add0689757110de4df276741299c2f0efec4d97a298aef"},"evidence_type":"test","evidence":{"statement":"producer integration"}}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(PRODUCER), "--ledger", str(ledger), "--entry", str(entry)], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            produced = json.loads(ledger.read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(produced["sequence"], 1)
            self.assertIsNone(produced["previous_entry_hash"])
            validation = self.validate({"contract_version":"1.0.0","entries":[produced]})
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)

if __name__ == "__main__":
    unittest.main()
