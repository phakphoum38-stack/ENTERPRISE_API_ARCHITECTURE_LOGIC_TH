from __future__ import annotations

import copy
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.validate_provenance_evidence import digest, plain_sha256

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_provenance_evidence.py"
PRODUCER = ROOT / "tools" / "record_provenance_entry.py"
FIXTURE = ROOT / "current" / "PROVENANCE_EVIDENCE_LEDGER_FIXTURE.json"
CONTRACT = ROOT / "current" / "PROVENANCE_EVIDENCE_CONTRACT.json"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
DOMAIN = b"provenance-entry-v1\x00"


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

    def test_target_commit_binding_accepts_exact_direct_attestation_target(self):
        ledger = self.load()
        target = ledger["entries"][0]["evidence"]["target_commit"]
        attestation = ledger["entries"][1]
        attestation["evidence"]["subject_id"] = target
        attestation["evidence"]["evidence_ids"] = []
        unsigned = dict(attestation)
        unsigned.pop("entry_hash", None)
        attestation["entry_hash"] = digest(unsigned)
        result = self.validate(ledger, target_commit=target)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_target_commit_binding_rejects_stale_direct_attestation_target(self):
        ledger = self.load()
        target = ledger["entries"][0]["evidence"]["target_commit"]
        stale_target = "f" * 40
        attestation = ledger["entries"][1]
        attestation["evidence"]["subject_id"] = stale_target
        unsigned = dict(attestation)
        unsigned.pop("entry_hash", None)
        attestation["entry_hash"] = digest(unsigned)
        result = self.validate(ledger, target_commit=target)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("attestation_target_commit_mismatch:EV-002", self.errors(result))

    def test_target_bound_roots_are_independently_verified_and_evidence_is_raw_bytes(self):
        ledger = self.load()
        target = ledger["entries"][0]["evidence"]["target_commit"]
        source = ledger["entries"][0]["evidence"]["source_commit"]
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            d = Path(d)
            evidence_path = d / "TARGET_BOUND_EVIDENCE.json"
            ledger_path = d / "TARGET_BOUND_PROVENANCE.json"
            roots_path = d / "TARGET_BOUND_ROOTS.json"
            evidence_bytes = json.dumps({"target_commit": target, "source_commit": source}, indent=2, sort_keys=True).encode("utf-8") + b"\n"
            evidence_path.write_bytes(evidence_bytes)
            ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            roots = {
                "schema_version": "1.0",
                "target_commit": target,
                "source_commit": source,
                "evidence_root": hashlib.sha256(evidence_bytes).hexdigest(),
                "provenance_root": plain_sha256(ledger),
                "evidence_file": str(evidence_path.relative_to(ROOT)).replace("\\", "/"),
                "provenance_file": str(ledger_path.relative_to(ROOT)).replace("\\", "/"),
            }
            roots_path.write_text(json.dumps(roots, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--contract", str(CONTRACT), "--ledger", str(ledger_path), "--roots", str(roots_path), "--target-commit", target],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)["roots_verified"])
            evidence_path.write_bytes(json.dumps({"source_commit": source, "target_commit": target}, separators=(",", ":")).encode("utf-8") + b"\n")
            tampered = subprocess.run(
                [sys.executable, str(VALIDATOR), "--contract", str(CONTRACT), "--ledger", str(ledger_path), "--roots", str(roots_path), "--target-commit", target],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(tampered.returncode, 0)
            self.assertIn("evidence_root_mismatch", self.errors(tampered))

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

    def test_artifact_digest_uses_raw_file_bytes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as d:
            d = Path(d)
            artifact = d / "artifact.json"
            original = b'{"a":1,"b":2}\n'
            reformatted = b'{\n  "b": 2,\n  "a": 1\n}\n'
            self.assertNotEqual(original, reformatted)
            self.assertEqual(json.loads(original), json.loads(reformatted))
            artifact.write_bytes(original)

            ledger = self.load()
            entry = copy.deepcopy(ledger["entries"][0])
            entry["evidence_type"] = "artifact"
            entry["evidence"] = {"statement": "raw-byte artifact regression"}
            entry["input_hashes"] = {
                "source": {
                    "algorithm": "git-sha1",
                    "digest": "0dc30f54f2205aa1f56ce881b3b8a2ba113d0a10",
                    "subject": "git-commit",
                }
            }
            entry["output_hashes"] = {
                "artifact": {
                    "algorithm": "sha256",
                    "digest": hashlib.sha256(original).hexdigest(),
                    "subject": f"artifact:{artifact.relative_to(ROOT)}",
                }
            }
            entry["previous_entry_hash"] = None
            unsigned = dict(entry)
            unsigned.pop("entry_hash", None)
            entry["entry_hash"] = hashlib.sha256(
                DOMAIN
                + json.dumps(unsigned, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            ).hexdigest()
            test_ledger = {"contract_version": "1.1.0", "entries": [entry]}

            artifact.write_bytes(reformatted)
            result = self.validate(test_ledger)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("derived_digest_mismatch:EV-001:artifact", self.errors(result))

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
