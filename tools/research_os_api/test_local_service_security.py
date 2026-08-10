from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class LocalServiceSecurityTests(unittest.TestCase):
    def test_packaged_windows_service_is_loopback_only_by_default(self):
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

    def test_non_loopback_primary_api_reuses_signed_identity_boundary(self):
        render_server = (
            ROOT / "tools" / "research_os_api" / "render_server.py"
        ).read_text(encoding="utf-8")
        service_auth = (
            ROOT / "tools" / "research_os_api" / "v2_service_auth.py"
        ).read_text(encoding="utf-8")

        self.assertIn("verify_service_request", render_server)
        self.assertIn("ServiceExposureAuthError", render_server)
        self.assertIn("X-ResearchOS-Identity-Signature", render_server)
        self.assertIn("IdentityAssertionVerifier", service_auth)
        self.assertIn("is_loopback_host", service_auth)
        self.assertIn("RESEARCH_OS_IDENTITY_PROXY_SECRET", service_auth)
        self.assertNotIn("X-ResearchOS-Identity-Secret", render_server)

    def test_upgrade_preserves_all_supported_service_provider_configuration(self):
        service_script = (ROOT / "scripts" / "research-os-service.ps1").read_text(
            encoding="utf-8"
        )
        installer = (ROOT / "installer" / "research-os.iss").read_text(
            encoding="utf-8"
        )

        self.assertIn("Get-PreservedProviderEnvironment", service_script)
        self.assertIn("PreservedProviderEnvironment", service_script)
        for name in (
            "RESEARCH_OS_PROVIDER",
            "RESEARCH_OS_SEARCH_PROVIDER",
            "RESEARCH_OS_OPENAI_API_KEY",
            "OPENAI_API_KEY",
            "RESEARCH_OS_OPENAI_ENDPOINT",
            "RESEARCH_OS_OPENAI_MODEL",
            "RESEARCH_OS_OPENAI_RESPONSES_ENDPOINT",
            "RESEARCH_OS_OPENAI_RESPONSES_MODEL",
            "RESEARCH_OS_GEMINI_API_KEY",
            "GEMINI_API_KEY",
            "RESEARCH_OS_GEMINI_ENDPOINT_TEMPLATE",
            "RESEARCH_OS_GEMINI_MODEL",
            "RESEARCH_OS_ANTHROPIC_API_KEY",
            "ANTHROPIC_API_KEY",
            "RESEARCH_OS_ANTHROPIC_ENDPOINT",
            "RESEARCH_OS_ANTHROPIC_MODEL",
        ):
            self.assertIn(f"'{name}'", service_script)
        self.assertIn("function PrepareToInstall", installer)
        self.assertIn("-Action stop", installer)


if __name__ == "__main__":
    unittest.main()
