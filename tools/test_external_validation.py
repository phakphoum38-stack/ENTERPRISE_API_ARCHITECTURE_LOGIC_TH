import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "external_validation.py"


class ExternalValidationPlaneTests(unittest.TestCase):
    def test_contract_declares_read_only_authority(self):
        contract = json.loads(
            (ROOT / "current" / "RESEARCH_OS_EXTERNAL_VALIDATION_CONTRACT.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(contract["authority_boundaries"]["may_validate"])
        self.assertFalse(contract["authority_boundaries"]["may_mutate_source"])
        self.assertFalse(contract["authority_boundaries"]["may_merge"])
        self.assertEqual(contract["authority_boundaries"]["release_authority"], "FINAL_GATE")
        self.assertEqual(contract["scope"]["excluded_path_policy"], "NEVER_SCAN")

    def test_runner_rejects_wrong_sha(self):
        result = subprocess.run(
            [sys.executable, str(RUNNER), "--source-sha", "0" * 40],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("source_sha_mismatch", result.stdout)

    def test_runner_passes_current_source_and_writes_evidence(self):
        sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "external-validation.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--source-sha",
                    sha,
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                timeout=120,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(evidence["source_sha"], sha)
            self.assertEqual(evidence["status"], "PASS")
            self.assertEqual(evidence["excluded_path_segment"], "efi")


if __name__ == "__main__":
    unittest.main()
