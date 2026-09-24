import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PlatformGovernanceTests(unittest.TestCase):
    def test_contract_is_active_and_fail_closed(self):
        contract = json.loads(
            (ROOT / "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json").read_text(encoding="utf-8")
        )
        self.assertEqual(contract["status"], "ACTIVE")
        self.assertEqual(contract["authority"]["release_authority"], "FINAL_GATE")
        self.assertFalse(contract["authority"]["may_release"])
        self.assertTrue(contract["authority"]["must_not_create_duplicate_authority"])
        self.assertTrue(contract["evidence_coverage"]["unknown_is_not_pass"])

    def test_validator_passes_against_canonical_sources(self):
        result = subprocess.run(
            [sys.executable, "tools/validate_platform_governance.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("RESEARCH_OS_PLATFORM_GOVERNANCE=PASS", result.stdout)

    def test_navigation_count_is_derived_not_hardcoded(self):
        source = (ROOT / "tools/validate_platform_governance.py").read_text(encoding="utf-8")
        self.assertNotIn("expected_destination_count", source)
        self.assertNotIn("range(17)", source)
        self.assertNotIn("range(18)", source)


if __name__ == "__main__":
    unittest.main()
