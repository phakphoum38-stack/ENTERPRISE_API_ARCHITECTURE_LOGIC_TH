"""Regression guards for V3 lifecycle ownership and data preservation.

These are source-level safety checks, not substitutes for the Windows runtime
lifecycle tests in the candidate and clean-core workflows.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE = ROOT / "v3" / "scripts" / "candidate_validate.ps1"
SERVICE = ROOT / "v3" / "scripts" / "v3-service.ps1"
CANDIDATE_WORKFLOW = ROOT / ".github" / "workflows" / "v3-candidate.yml"
CLEAN_CORE_WORKFLOW = ROOT / ".github" / "workflows" / "v3-clean-core.yml"


class V3LifecycleSafetyTests(unittest.TestCase):
    def test_candidate_never_erases_programdata_and_seeds_preservation_sentinel_first(self):
        source = CANDIDATE.read_text(encoding="utf-8")
        self.assertNotIn("Remove-Item $dataDir -Recurse -Force", source)
        seed = source.index("Set-Content -Path $marker -Value 'preserve-v3-candidate-data'")
        stale_cleanup_call = source.index("    Remove-StaleInstallation\n")
        self.assertLess(seed, stale_cleanup_call)
        self.assertIn("Assert-Marker $marker 'preserve-v3-candidate-data'", source)

    def test_candidate_validation_supports_local_windows_without_runner_temp(self):
        source = CANDIDATE.read_text(encoding="utf-8")
        self.assertIn("$tempRoot = $env:RUNNER_TEMP", source)
        self.assertIn("[System.IO.Path]::GetTempPath()", source)
        self.assertNotIn("Join-Path $env:RUNNER_TEMP", source)

    def test_service_cleanup_never_kills_a_listener_by_port_alone(self):
        source = SERVICE.read_text(encoding="utf-8")
        self.assertNotIn("Stop-Process -Id $listener.OwningProcess", source)
        self.assertIn("refusing to terminate unrelated listeners", source)
        self.assertIn("Port must be between 1 and 65535", source)
        self.assertIn("WaitForStatus('Stopped'", source)

    def test_candidate_cleanup_fails_instead_of_killing_unowned_listener(self):
        source = CANDIDATE_WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("Stop-Process -Id $listener.OwningProcess", source)
        self.assertIn("refusing to terminate unrelated listeners", source)
        self.assertNotIn("catch { }", source[source.index("- name: Final candidate cleanup"):])


    def test_service_cleanup_verifies_image_path_before_stop_or_delete(self):
        source = SERVICE.read_text(encoding="utf-8")
        self.assertIn("function Assert-V3ServiceOwnership", source)
        self.assertIn("Win32_Service", source)
        self.assertIn("Refusing to modify service", source)
        self.assertIn("function Test-V3ProcessDescendant", source)
        self.assertIn("Assert-V3OwnedLoopbackListener", source)
        self.assertIn("Automatic rollback was incomplete", source)

    def test_candidate_cleanup_verifies_service_identity_and_listener_owner(self):
        source = CANDIDATE.read_text(encoding="utf-8")
        self.assertIn("function Assert-ExistingV3ServiceOwnership", source)
        self.assertIn("function Test-V3ProcessDescendant", source)
        self.assertIn("Assert-V3OwnedLoopbackListener", source)
        self.assertIn("Refusing to modify service", source)

    def test_clean_core_runs_on_pull_requests_and_does_not_delete_unknown_service(self):
        source = CLEAN_CORE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("  pull_request:", source)
        self.assertIn('$env:GITHUB_RUN_ID', source)
        self.assertIn("Refusing to modify CI service", source)
        self.assertIn("$createdByThisRun", source)
        self.assertIn("set -euo pipefail", source)
        self.assertIn("Failed to record Windows service lifecycle evidence", source)

    def test_clean_core_uses_dynamic_e2e_port_and_preserves_foreign_listeners(self):
        source = CLEAN_CORE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('$env:RESEARCH_OS_V3_PORT = "$port"', source)
        self.assertNotIn("http://127.0.0.1:8788/health", source)
        self.assertNotIn("Stop-Process -Id $connection.OwningProcess", source)
        self.assertIn("refusing to terminate unrelated listeners", source)
        self.assertIn("data_preserved", source)


if __name__ == "__main__":
    unittest.main()
