from pathlib import Path
import unittest


class OwnerInstallerQuiesceGuardTest(unittest.TestCase):
    def setUp(self):
        self.source = (
            Path(__file__).resolve().parents[1]
            / "installer"
            / "scripts"
            / "research-os-owner-runtime-quiesce.ps1"
        )
        self.text = self.source.read_text(encoding="utf-8")

    def test_listener_cleanup_verifies_process_identity_before_kill(self):
        text = self.text

        self.assertIn(
            'function Stop-OwnerProcess',
            text,
        )
        self.assertIn(
            'Get-CimInstance Win32_Process',
            text,
        )
        self.assertIn(
            'Normalize-Path $process.ExecutablePath',
            text,
        )
        self.assertIn(
            '$targets -icontains $full',
            text,
        )
        self.assertIn(
            'Refusing to terminate foreign process',
            text,
        )
        self.assertIn(
            'taskkill.exe',
            text,
        )

        identity_guard = text.index('$targets -icontains $full')
        kill_command = text.index('taskkill.exe')

        self.assertLess(
            identity_guard,
            kill_command,
            'Process identity must be verified before taskkill.exe is invoked.',
        )

    def test_listener_pid_is_not_killed_without_the_guard(self):
        text = self.text

        self.assertIn(
            'Stop-OwnerProcess -ProcessId $listenerPid',
            text,
        )
        self.assertIn(
            'Get-CimInstance Win32_Process',
            text,
        )
        self.assertIn(
            '$targets -icontains $full',
            text,
        )
        self.assertIn(
            'Refusing to terminate foreign process.',
            text,
        )

        listener_stop = text.index(
            'Stop-OwnerProcess -ProcessId $listenerPid'
        )
        identity_guard = text.index(
            '$targets -icontains $full'
        )

        self.assertLess(
            identity_guard,
            listener_stop,
            'Listener PID must pass the identity guard before termination.',
        )


if __name__ == "__main__":
    unittest.main()
