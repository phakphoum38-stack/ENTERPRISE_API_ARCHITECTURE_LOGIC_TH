import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "validate_aeos_source_checks.py"
REGISTRY = ROOT / "current" / "AEOS_ASSURANCE_CHECK_REGISTRY.json"
EXTENDED = ROOT / "owner_special" / "research_os_friend" / "aeos_extended_assurance_checks.py"
SEMANTIC = ROOT / "owner_special" / "research_os_friend" / "aeos_source_semantic_checks.py"


class AeosSourceCheckAuditTests(unittest.TestCase):
    def test_registry_has_explicit_source_test_semantics(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(payload["policy"], "fail_closed")
        checks = payload["checks"]
        self.assertEqual(len(checks), 83)
        self.assertEqual(len({check["id"] for check in checks}), 83)
        for check in checks:
            self.assertIn("id", check)
            mode = check.get("verification_mode", "source")
            if mode == "source":
                self.assertTrue(check.get("boundary"), check["id"])
            elif mode == "external_evidence":
                self.assertIsNone(check.get("boundary"), check["id"])
            else:
                self.fail(f"unknown verification mode: {check['id']}")

    def test_contract_conformance_is_executable_source(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        check = next(item for item in payload["checks"] if item["id"] == "CONTRACT_CONFORMANCE")
        self.assertEqual(
            check["boundary"],
            "owner_special/research_os_friend/aeos_contract_conformance.py",
        )
        self.assertEqual(check["required_symbols"], ["contract_conformance"])

    def test_extended_observation_wrappers_are_not_certifying_boundaries(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        module_path = "owner_special/research_os_friend/aeos_extended_assurance_checks.py"
        checks = [item for item in payload["checks"] if item.get("boundary") == module_path]
        self.assertEqual(checks, [])
        self.assertTrue(EXTENDED.is_file())

    def test_source_semantic_boundary_is_registered(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        module_path = "owner_special/research_os_friend/aeos_source_semantic_checks.py"
        checks = [item for item in payload["checks"] if item.get("boundary") == module_path]
        self.assertEqual(len(checks), 40)
        source = SEMANTIC.read_text(encoding="utf-8")
        for check in checks:
            symbols = check.get("required_symbols")
            self.assertEqual(len(symbols), 1, check["id"])
            self.assertIn(f"def {symbols[0]}(", source, check["id"])

    def test_source_audit_is_fail_closed_on_semantic_gaps(self):
        proc = subprocess.run(
            [sys.executable, str(TOOL)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        report = json.loads(proc.stdout.strip().splitlines()[-1])
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(report["checks"], 83)
        self.assertEqual(report["executable_source_checks"], 83)
        self.assertEqual(report["external_evidence_checks"], 0)
        self.assertTrue(any(error.startswith("source_semantic_gap:") for error in report["errors"]))
        self.assertTrue(any(error.startswith("source_semantic_gap:SEMANTIC_COMPATIBILITY:") for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
