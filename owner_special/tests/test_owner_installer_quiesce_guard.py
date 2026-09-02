from pathlib import Path
import unittest


class OwnerInstallerQuiesceGuardTest(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.source = (
            self.root
            / "installer"
            / "scripts"
            / "research-os-owner-runtime-quiesce.ps1"
        )
        self.installer = self.root / "installer" / "owner-special.iss"
        self.text = self.source.read_text(encoding="utf-8-sig")
        self.installer_text = self.installer.read_text(encoding="utf-8-sig")

    def test_listener_cleanup_verifies_process_identity_before_kill(self):
        text = self.text

        self.assertIn('function Stop-OwnerProcess', text)
        self.assertIn('Get-CimInstance Win32_Process', text)
        self.assertIn('Normalize-Path $process.ExecutablePath', text)
        self.assertIn('$targets -icontains $full', text)
        self.assertIn('Refusing to terminate foreign process', text)
        self.assertIn('taskkill.exe', text)

        identity_guard = text.index('$targets -icontains $full')
        kill_command = text.index('taskkill.exe')

        self.assertLess(
            identity_guard,
            kill_command,
            'Process identity must be verified before taskkill.exe is invoked.',
        )

    def test_listener_pid_is_not_killed_without_the_guard(self):
        text = self.text

        self.assertIn('Stop-OwnerProcess -ProcessId $listenerPid', text)
        self.assertIn('Get-CimInstance Win32_Process', text)
        self.assertIn('$targets -icontains $full', text)
        self.assertIn('Refusing to terminate foreign process.', text)

        listener_stop = text.index('Stop-OwnerProcess -ProcessId $listenerPid')
        identity_guard = text.index('$targets -icontains $full')

        self.assertLess(
            identity_guard,
            listener_stop,
            'Listener PID must pass the identity guard before termination.',
        )

    def test_quiesce_helper_writes_diagnostics_and_preserves_exit_semantics(self):
        text = self.text

        self.assertIn("[string]$LogPath = (Join-Path $env:TEMP 'ResearchOS-Owner-Quiesce.log')", text)
        self.assertIn('function Write-Diagnostic', text)
        self.assertIn('Add-Content -LiteralPath $LogPath', text)
        self.assertIn('$taskkillExitCode = $LASTEXITCODE', text)
        self.assertIn('taskkill failed for verified Owner process', text)
        self.assertIn('Owner runtime could not be safely quiesced. EXITCODE=5', text)
        self.assertIn('Unhandled quiesce helper error:', text)
        self.assertIn('Owner runtime quiesce helper aborted. EXITCODE=1', text)

    def test_installer_passes_diagnostic_log_path_and_reports_it(self):
        text = self.installer_text

        self.assertIn('QuiesceLogPath :=', text)
        self.assertIn("ExpandConstant('{%TEMP}') + '\\ResearchOS-Owner-Quiesce.log'", text)
        self.assertIn("' -LogPath \"' + QuiesceLogPath + '\"'", text)
        self.assertIn('Owner quiesce diagnostic log:', text)
        self.assertIn('Detailed diagnostic:', text)


if __name__ == "__main__":
    unittest.main()
