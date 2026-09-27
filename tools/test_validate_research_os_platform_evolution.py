import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class PlatformEvolutionTests(unittest.TestCase):
    def test_evolution_validation_passes(self):
        result = subprocess.run(
            [sys.executable, "tools/validate_research_os_platform_evolution.py"],
            cwd=ROOT, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PLATFORM_EVOLUTION=PASS", result.stdout)

    def test_evolution_does_not_create_authority(self):
        import json
        contract = json.loads((ROOT / "current/RESEARCH_OS_PLATFORM_EVOLUTION_CONTRACT.json").read_text())
        authority = contract["authority"]
        self.assertEqual(authority["release_authority"], "FINAL_GATE")
        for key in ("may_execute","may_authorize","may_approve","may_merge","may_release"):
            self.assertFalse(authority[key])

    def test_high_impact_is_fail_closed(self):
        import json
        contract = json.loads((ROOT / "current/RESEARCH_OS_PLATFORM_EVOLUTION_CONTRACT.json").read_text())
        self.assertEqual(contract["evolution"]["impact"]["unknown"], "HOLD")
        self.assertEqual(contract["evolution"]["simulation"]["required_for"], "CROSS_PROJECT")

if __name__ == "__main__":
    unittest.main()
