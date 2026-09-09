from __future__ import annotations

import copy
import json
import re
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
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ProvenanceEvidenceTests(unittest.TestCase):
    def load(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def validate(self, ledger, target_commit=None):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as f:
            json.dump(ledger, f)
            path = Path(f.name)
        try:
            cmd = [sys.executable, str(VALIDATOR), "--contract", str(CONTRACT), "--ledger", str(path)]
            if target_commit:
                cmd += ["--target-commit", target_commit]
            return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        finally:
            path.unlink(missing_ok=True)

    def errors(self, result):
        return json.loads(result.stdout)["errors"]

    def test_canonical_fixture_passes(self):
        result = subprocess.run([sys.executable, str(VALIDATOR)], cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_git_sha1_is_never_accepted_as_artifact_sha256(self):
        ledger = self.load()
        record = ledger["entries"][0]["output_hashes"]["contract"]
        record["algorithm"] = "git-sha1"
        record["digest"] = "0dc30f54f2205aa1f56ce881b3b8a2ba113d0a10"
        record["subject"] = "artifact:current/PROVENANCE_EVIDENCE_CONTRACT.json"
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("git_sha1_wrong_identity:EV-001:output_hashes.contract", self.errors(result))

    def test_wrong_digest_length_is_rejected_without_normalization(self):
        ledger = self.load()
        record = ledger["entries"][0]["output_hashes"]["contract"]
        record["digest"] = record["digest"][:-1]
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_sha256:EV-001:output_hashes.contract", self.errors(result))

    def test_target_commit_binding_rejects_stale_evidence(self):
        ledger = self.load()
        target = ledger["entries"][0]["evidence"]["target_commit"]
        stale_target = "f" * 40
        self.assertNotEqual(target, stale_target)
        result = self.validate(ledger, target_commit=stale_target)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("target_commit_mismatch:EV-001", self.errors(result))

    def test_target_commit_binding_accepts_exact_target(self):
        ledger = self.load()
        target = ledger["entries"][0]["evidence"]["target_commit"]
        result = self.validate(ledger, target_commit=target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_payload_or_evidence_tamper_breaks_entry_hash(self):
        ledger = self.load()
        ledger["entries"][0]["evidence"]["reason"] = "tampered"
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("entry_hash_mismatch:EV-001", self.errors(result))

    def test_chain_tamper_breaks_previous_hash(self):
        ledger = self.load()
        ledger["entries"][1]["previous_entry_hash"] = "0" * 64
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("previous_hash_mismatch:EV-002", self.errors(result))

    def test_sequence_gap_fails_closed(self):
        ledger = self.load()
        ledger["entries"][1]["sequence"] = 3
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("invalid_sequence:EV-002", self.errors(result))

    def test_duplicate_entry_id_fails_closed(self):
        ledger = self.load()
        ledger["entries"].append(copy.deepcopy(ledger["entries"][0]))
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate_entry_id:EV-001", self.errors(result))

    def test_unknown_evidence_reference_fails_closed(self):
        ledger = self.load()
        ledger["entries"][0]["evidence"]["evidence_ids"] = ["EV-999"]
        result = self.validate(ledger)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown_evidence_reference:EV-001", self.errors(result))

    def test_producer_rejects_caller_supplied_derived_fields(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            ledger = d / "ledger.json"
            entry = d / "entry.json"
            ledger.write_text(json.dumps({"contract_version": "1.1.0", "entries": []}), encoding="utf-8")
            entry.write_text(json.dumps({"entry_id": "EV-BAD", "sequence": 99}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(PRODUCER), "--ledger", str(ledger), "--entry", str(entry)], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("derived_fields_must_not_be_supplied", result.stdout)

    def test_producer_output_is_deterministic_and_verifiable(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            ledger = d / "ledger.json"
            entry = d / "entry.json"
            ledger.write_text(json.dumps({"contract_version": "1.1.0", "entries": []}), encoding="utf-8")
            entry.write_text(json.dumps({"entry_id":"EV-PRODUCER","recorded_at":"2026-09-09T00:00:00Z","actor_id":"H-OWNER","action":"test","subject_type":"test","subject_id":"T-001","input_hashes":{"source":{"algorithm":"git-sha1","digest":"0dc30f54f2205aa1f56ce881b3b8a2ba113d0a10","subject":"git-commit"}},"output_hashes":{"result":{"algorithm":"sha256","digest":"47f4a45784e11bbc22b9cfae7c18a598519bce6eb5d9837a650b0782071ca07b","subject":"test-output"}},"evidence_type":"test","evidence":{"statement":"producer integration"}}), encoding="utf-8")
            result = subprocess.run([sys.executable, str(PRODUCER), "--ledger", str(ledger), "--entry", str(entry)], cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            produced = json.loads(ledger.read_text(encoding="utf-8"))["entries"][0]
            self.assertEqual(produced["sequence"], 1)
            self.assertIsNone(produced["previous_entry_hash"])
            self.assertRegex(produced["entry_hash"], HEX64)
            validation = self.validate({"contract_version":"1.1.0","entries":[produced]})
            self.assertEqual(validation.returncode, 0, validation.stdout + validation.stderr)


if __name__ == "__main__":
    unittest.main()