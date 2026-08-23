from __future__ import annotations

import unittest
from pathlib import Path


class WindowsLoopbackSecurityTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[2]

    def test_windows_setup_defaults_api_to_loopback(self) -> None:
        script = (self.ROOT / "scripts" / "setup-research-os-windows.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            '[Environment]::SetEnvironmentVariable("RESEARCH_OS_API_HOST", "127.0.0.1", "User")',
            script,
        )
        self.assertNotIn(
            '[Environment]::SetEnvironmentVariable("RESEARCH_OS_API_HOST", "0.0.0.0", "User")',
            script,
        )

    def test_windows_service_preserves_explicit_host_override(self) -> None:
        program = (self.ROOT / "tools" / "research_os_service" / "Program.cs").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            'Environment.GetEnvironmentVariable("RESEARCH_OS_API_HOST") ?? "127.0.0.1"',
            program,
        )
        self.assertIn('Environment.GetEnvironmentVariable("RESEARCH_OS_API_HOST")', program)


if __name__ == "__main__":
    unittest.main()
