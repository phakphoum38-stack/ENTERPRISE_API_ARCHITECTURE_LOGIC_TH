import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTRACTS = (
    "current/RESEARCH_OS_PLATFORM_DEFECT_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_SCHEDULE_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_RISK_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_CHANGE_IMPACT_CONTRACT.json",
)

class PlatformOperatingControlTests(unittest.TestCase):
    def test_control_contracts_are_active_and_fail_closed(self):
        for path in CONTRACTS:
            data = json.loads((ROOT / path).read_text(encoding="utf-8"))
            self.assertEqual(data["status"], "ACTIVE")
            self.assertTrue(data["authority"]["descriptive_only"])
            self.assertFalse(data["authority"]["may_execute"])
            self.assertFalse(data["authority"]["may_authorize"])
            self.assertFalse(data["authority"]["may_approve"])
            self.assertFalse(data["authority"]["may_merge"])
            self.assertFalse(data["authority"]["may_release"])
            self.assertEqual(data["authority"]["release_authority"], "FINAL_GATE")

    def test_change_impact_uses_existing_governance_engine(self):
        result = subprocess.run(
            [sys.executable, "tools/platform_change_impact.py",
             "current/RESEARCH_OS_PLATFORM_CHANGE_IMPACT_CONTRACT.json"],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertIn("change_impact_control", payload["affected_components"])
        self.assertIn("unified_final_gate", payload["required_gates"])

if __name__ == "__main__":
    unittest.main()
