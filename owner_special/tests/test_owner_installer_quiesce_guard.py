from pathlib import Path
import unittest


class OwnerInstallerQuiesceGuardTest(unittest.TestCase):
    def test_listener_cleanup_verifies_process_identity_before_kill(self):
        source = Path(__file__).resolve().parents[1] / "installer" / "owner-special.iss"
        text = source.read_text(encoding="utf-8")

        stop_start = text.index("function Stop-OwnerProcess")
        stop_end = text.index("'try {'", stop_start)
        stop_function = text[stop_start:stop_end]

        self.assertIn('Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId"', stop_function)
        self.assertIn("Normalize-Path $process.ExecutablePath", stop_function)
        self.assertIn("$targets -icontains $full", stop_function)
        self.assertIn("Refusing to terminate foreign process", stop_function)
        self.assertLess(stop_function.index("$targets -icontains $full"), stop_function.index("taskkill.exe"))

    def test_listener_pid_is_not_killed_without_the_guard(self):
        source = Path(__file__).resolve().parents[1] / "installer" / "owner-special.iss"
        text = source.read_text(encoding="utf-8")

        listener_block_start = text.index("$listenerPids =")
        listener_block_end = text.index("Start-Sleep -Milliseconds 500", listener_block_start)
        listener_block = text[listener_block_start:listener_block_end]

        self.assertIn("Stop-OwnerProcess -ProcessId $listenerPid", listener_block)
        stop_start = text.index("function Stop-OwnerProcess")
        stop_end = text.index("'try {'", stop_start)
        stop_function = text[stop_start:stop_end]
        self.assertIn("Get-CimInstance Win32_Process", stop_function)
        self.assertIn("$targets -icontains $full", stop_function)


if __name__ == "__main__":
    unittest.main()
