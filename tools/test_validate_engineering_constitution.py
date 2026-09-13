import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_engineering_constitution.py"
CONSTITUTION = ROOT / "current" / "ENGINEERING_CONSTITUTION.json"
FIXTURE = ROOT / "current" / "ENGINEERING_CONSTITUTION_FIXTURE.json"


class EngineeringConstitutionValidatorTests(unittest.TestCase):
    def run_validator(self, constitution: Path, fixture: Path | None = None):
        command = [sys.executable, str(VALIDATOR), "--constitution", str(constitution)]
        if fixture:
            command += ["--fixture", str(fixture)]
        return subprocess.run(command, cwd=ROOT, capture_output=True, text=True)

    def test_canonical_constitution_and_fixture_pass(self):
        result = self.run_validator(CONSTITUTION, FIXTURE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "PASS")

    def test_self_grant_authority_fails_closed(self):
        payload = json.loads(CONSTITUTION.read_text(encoding="utf-8"))
        payload["governance_rules"]["workflow_self_grant_authority"] = True
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "constitution.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_validator(path)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")

    def test_missing_human_authority_fails_closed(self):
        payload = json.loads(CONSTITUTION.read_text(encoding="utf-8"))
        payload["authority_levels"] = [x for x in payload["authority_levels"] if x["id"] != "human_owner"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "constitution.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_validator(path)
        self.assertNotEqual(result.returncode, 0)
        report = json.loads(result.stdout)
        self.assertIn("human_owner authority is mandatory", report["errors"])

    def test_invalid_amendment_approval_fails_closed(self):
        payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
        payload["amendments"][0]["approval"]["status"] = "pending"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            result = self.run_validator(CONSTITUTION, path)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
