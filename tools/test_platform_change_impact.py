import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PlatformChangeImpactTests(unittest.TestCase):
    def test_navigation_change_expands_to_surface_and_gates(self):
        result = subprocess.run(
            [sys.executable, "tools/platform_change_impact.py",
             "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart"],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertIn("navigation", payload["affected_components"])
        self.assertIn("unified_final_gate", payload["required_gates"])

    def test_unknown_path_has_no_invented_impact(self):
        result = subprocess.run(
            [sys.executable, "tools/platform_change_impact.py", "docs/unrelated.txt"],
            cwd=ROOT, text=True, capture_output=True, check=True,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["affected_components"], [])
        self.assertEqual(payload["required_gates"], [])

    def test_rules_are_contract_driven(self):
        source = (ROOT / "tools/platform_change_impact.py").read_text(encoding="utf-8")
        self.assertNotIn("range(17)", source)
        self.assertNotIn("range(18)", source)


if __name__ == "__main__":
    unittest.main()
