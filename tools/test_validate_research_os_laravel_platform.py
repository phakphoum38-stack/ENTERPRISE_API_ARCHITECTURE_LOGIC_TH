import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LaravelPlatformBoundaryTest(unittest.TestCase):
    def test_contract_is_fail_closed_and_versioned(self):
        contract = json.loads(
            (ROOT / "current/RESEARCH_OS_LARAVEL_PLATFORM_CONTRACT.json").read_text()
        )
        self.assertEqual(contract["version"], "1.0.0")
        self.assertFalse(contract["delivery"]["direct_engine_to_runner"])
        self.assertTrue(contract["delivery"]["idempotency_required"])
        self.assertTrue(contract["delivery"]["resource_conflict_fail_closed"])

    def test_runtime_surface_exists(self):
        app = ROOT / "apps/research_os_laravel"
        for relative in (
            "composer.json",
            "artisan",
            "bootstrap/app.php",
            "routes/api.php",
            "src/Platform/Contracts/AuthorizationGateway.php",
            "src/Platform/Contracts/WorkflowGateway.php",
        ):
            self.assertTrue((app / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
