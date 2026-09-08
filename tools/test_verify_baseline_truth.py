import json
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("verify_baseline_truth.py")
CONTRACT = Path(__file__).parents[1] / "current" / "BASELINE_TRUTH_CONTRACT.json"


class BaselineTruthVerifierTests(unittest.TestCase):
    def test_contract_contains_distinct_truth_anchors(self):
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        production = contract["production_code_truth"]["commit"]
        canonical = contract["canonical_main_history_truth"]["commit"]
        self.assertRegex(production, r"^[0-9a-f]{40}$")
        self.assertRegex(canonical, r"^[0-9a-f]{40}$")
        self.assertNotEqual(production, canonical)

    def test_verifier_reports_pass_for_known_anchors(self):
        result = subprocess.run(
            ["python", str(SCRIPT), "--head", "fab39afc15739c3dc9952f6f21db46d26f54b683"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"status":"PASS"', result.stdout)
        self.assertIn("BASELINE_TRUTH_GATE=PASS", result.stdout)

    def test_missing_commit_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            contract = Path(temp_dir) / "contract.json"
            contract.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "production_code_truth": {"commit": "0" * 40},
                        "canonical_main_history_truth": {"commit": "1" * 40},
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python", str(SCRIPT), "--contract", str(contract), "--head", "1" * 40],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL")
            self.assertIn(
                "production commit missing: " + "0" * 40,
                payload["failures"],
            )
            self.assertIn(
                "canonical commit missing: " + "1" * 40,
                payload["failures"],
            )


if __name__ == "__main__":
    unittest.main()
