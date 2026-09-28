import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class IdentityAccessWave1ValidatorTest(unittest.TestCase):
    def test_wave1_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/validate_research_os_identity_access_wave1.py")],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("IDENTITY_ACCESS_WAVE_1=PASS", result.stdout)
        self.assertIn("GOOGLE_SIGN_IN_CAPABILITY=HOLD", result.stdout)

if __name__ == "__main__":
    unittest.main()
