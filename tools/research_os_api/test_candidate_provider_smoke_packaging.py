from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class CandidateProviderSmokePackagingTests(unittest.TestCase):
    def test_candidate_package_includes_live_service_provider_smoke(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "candidate.yml").read_text(
            encoding="utf-8"
        )
        smoke = ROOT / "tools" / "research_os_api" / "service_provider_smoke.py"
        wrapper = ROOT / "scripts" / "test-research-os-provider-service.ps1"

        self.assertTrue(smoke.is_file())
        self.assertTrue(wrapper.is_file())
        self.assertIn(
            'Copy-Item "tools\\research_os_api\\*.py" "$package\\tools\\research_os_api" -Force',
            workflow,
        )
        self.assertIn(
            'Copy-Item "scripts\\*research-os*.ps1" "$package\\scripts" -Force',
            workflow,
        )
        self.assertIn("service_provider_smoke.py", wrapper.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
