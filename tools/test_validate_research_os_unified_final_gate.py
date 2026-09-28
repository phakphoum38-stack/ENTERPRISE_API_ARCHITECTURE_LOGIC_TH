import unittest
from pathlib import Path
import subprocess
import sys


class UnifiedFinalGateValidatorTest(unittest.TestCase):
    def test_validator_passes_on_current_source(self) -> None:
        root = Path(__file__).resolve().parents[1]
        script = root / "tools" / "validate_research_os_unified_final_gate.py"
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=root,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("UNIFIED_FINAL_GATE_CONTRACT=PASS", result.stdout)
        self.assertIn("AEOS_RECHECK=BOUND_TO_FINAL_GATE", result.stdout)
        self.assertIn("AEOS_RELEASE_AUTHORITY=FINAL_GATE", result.stdout)
        self.assertIn("RUNTIME_RESOLUTION=BOUND_TO_PLATFORM", result.stdout)


if __name__ == "__main__":
    unittest.main()
