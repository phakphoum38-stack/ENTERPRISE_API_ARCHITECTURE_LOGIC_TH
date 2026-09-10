import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "validate_aeos_source_checks.py"
REGISTRY = ROOT / "current" / "AEOS_ASSURANCE_CHECK_REGISTRY.json"


class AeosSourceCheckAuditTests(unittest.TestCase):
    def test_registry_has_explicit_source_test_semantics(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(payload["policy"], "fail_closed")
        checks = payload["checks"]
        self.assertTrue(checks)
        for check in checks:
            self.assertIn("id", check)
            # Until every assurance item has a real source-level executor,
            # a missing boundary is intentionally a FAIL, never a PASS.
            if check.get("verification_mode", "source") == "source":
                self.assertTrue(check.get("boundary"), check["id"])

    def test_contract_conformance_is_executable_source(self):
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
        check = next(item for item in payload["checks"] if item["id"] == "CONTRACT_CONFORMANCE")
        self.assertEqual(
            check["boundary"],
            "owner_special/research_os_friend/aeos_contract_conformance.py",
        )
        self.assertEqual(check["required_symbols"], ["contract_conformance"])

    def test_source_audit_is_fail_closed(self):
        proc = subprocess.run(
            [sys.executable, str(TOOL)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        report = json.loads(proc.stdout.strip().splitlines()[-1])
        # Current registry deliberately exposes unfinished source-level checks;
        # the audit must surface them instead of silently certifying them.
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(report["status"], "FAIL")
        self.assertGreater(len(report["errors"]), 0)
        self.assertGreater(report["checks"], 0)
        self.assertFalse(any("CONTRACT_CONFORMANCE" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
