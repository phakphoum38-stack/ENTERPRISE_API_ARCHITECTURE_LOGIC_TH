import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_PLATFORM_RUNTIME_RESOLUTION_CONTRACT.json"
VALIDATOR = ROOT / "tools" / "validate_platform_runtime_resolution.py"


class PlatformRuntimeResolutionContractTest(unittest.TestCase):
    def test_validator_passes(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PLATFORM_RUNTIME_RESOLUTION=PASS", result.stdout)

    def test_contract_is_fail_closed(self):
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
        self.assertEqual(data["surface_matrix"]["unknown_surface"], "STOP")
        self.assertEqual(data["path_resolution"]["must_reject_path_traversal"], True)
        self.assertEqual(data["runtime_selection"]["engine_to_runner_direct_call_forbidden"], True)
        self.assertEqual(data["local_compute"]["m2_is_authorization"], False)
        self.assertEqual(data["local_compute"]["m2_is_release_authority"], False)

    def test_conflict_policy_preserves_stop_release_reconcile(self):
        conflict = json.loads(CONTRACT.read_text(encoding="utf-8"))["resource_conflict"]
        self.assertEqual(conflict["policy"], "REJECT")
        self.assertTrue(conflict["stop_execution"])
        self.assertTrue(conflict["release_resources"])
        self.assertTrue(conflict["ack_or_reconcile_delivery"])
        self.assertFalse(conflict["same_version_overwrite"])
        self.assertTrue(conflict["alternate_version_branching_allowed"])


if __name__ == "__main__":
    unittest.main()
