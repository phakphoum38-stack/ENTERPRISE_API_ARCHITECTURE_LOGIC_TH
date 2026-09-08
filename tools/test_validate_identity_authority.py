from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_identity_authority.py"
CONTRACT = ROOT / "current" / "IDENTITY_AUTHORITY_CONTRACT.json"
FIXTURE = ROOT / "current" / "IDENTITY_AUTHORITY_FIXTURE.json"


class IdentityAuthorityValidatorTests(unittest.TestCase):
    def run_validator(self, fixture: dict, contract_path: Path = CONTRACT):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as handle:
            json.dump(fixture, handle)
            fixture_path = Path(handle.name)
        try:
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--contract", str(contract_path), "--fixture", str(fixture_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            payload = json.loads(result.stdout)
            return result, payload
        finally:
            fixture_path.unlink(missing_ok=True)

    def load_fixture(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_canonical_fixture_passes(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)], cwd=ROOT, capture_output=True, text=True, check=False
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_duplicate_proof_id_fails_closed(self):
        fixture = self.load_fixture()
        fixture["authorization_proofs"][1]["proof_id"] = fixture["authorization_proofs"][0]["proof_id"]
        result, payload = self.run_validator(fixture)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate_proof_id:P-001", payload["errors"])

    def test_self_grant_fails_closed(self):
        fixture = self.load_fixture()
        fixture["grants"][0]["granted_by"] = fixture["grants"][0]["subject_id"]
        result, payload = self.run_validator(fixture)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("self_grant:G-001", payload["errors"])

    def test_revoked_identity_cannot_receive_grant(self):
        fixture = self.load_fixture()
        fixture["grants"][0]["subject_id"] = "A-REVOKED"
        result, payload = self.run_validator(fixture)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("grant_to_revoked_identity:G-001", payload["errors"])

    def test_scope_escalation_fails_closed(self):
        fixture = self.load_fixture()
        fixture["grants"][0]["scope"] = {"repository": "all"}
        result, payload = self.run_validator(fixture)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("grant_scope_escalation:G-001", payload["errors"])

    def test_allow_without_active_grant_fails_closed(self):
        fixture = self.load_fixture()
        fixture["authorization_proofs"][0]["capability_id"] = "CAP-PROD-MUTATE"
        result, payload = self.run_validator(fixture)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("allow_without_active_grant:P-001", payload["errors"])

    def test_unknown_identity_fails_closed(self):
        fixture = self.load_fixture()
        fixture["authorization_proofs"][0]["subject_id"] = "A-UNKNOWN"
        result, payload = self.run_validator(fixture)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown_proof_subject:P-001", payload["errors"])

    def test_missing_contract_fails_closed_with_structured_report(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", encoding="utf-8", delete=False) as handle:
            handle.write("{}")
            contract_path = Path(handle.name)
        try:
            result, payload = self.run_validator(self.load_fixture(), contract_path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("contract_not_canonical", payload["errors"])
        finally:
            contract_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
