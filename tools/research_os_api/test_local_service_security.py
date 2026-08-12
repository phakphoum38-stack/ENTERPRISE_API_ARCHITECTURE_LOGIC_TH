from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class LocalServiceSecurityTests(unittest.TestCase):
    def test_packaged_windows_service_is_loopback_only(self):
        service_script = (ROOT / "scripts" / "research-os-service.ps1").read_text(
            encoding="utf-8"
        )
        service_host = (
            ROOT / "tools" / "research_os_service" / "Program.cs"
        ).read_text(encoding="utf-8")
        render_server = (
            ROOT / "tools" / "research_os_api" / "render_server.py"
        ).read_text(encoding="utf-8")

        self.assertIn("RESEARCH_OS_API_HOST=127.0.0.1", service_script)
        self.assertNotIn("RESEARCH_OS_API_HOST=0.0.0.0", service_script)
        self.assertIn('?? "127.0.0.1"', service_host)
        self.assertIn('os.getenv("HOST", "127.0.0.1")', render_server)

    def test_upgrade_preserves_service_scoped_provider_configuration(self):
        service_script = (ROOT / "scripts" / "research-os-service.ps1").read_text(
            encoding="utf-8"
        )
        installer = (ROOT / "installer" / "research-os.iss").read_text(
            encoding="utf-8"
        )

        self.assertIn("Get-PreservedProviderEnvironment", service_script)
        self.assertIn("PreservedProviderEnvironment", service_script)
        self.assertIn("function PrepareToInstall", installer)
        self.assertIn("-Action stop", installer)


if __name__ == "__main__":
    unittest.main()
