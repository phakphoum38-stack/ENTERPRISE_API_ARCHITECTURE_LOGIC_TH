from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from research_os_friend.provider_settings import MemorySecretStore, ProviderManager


class LaunchDeskProviderContractTests(unittest.TestCase):
    def test_existing_provider_can_supply_runtime_config_without_safe_status_exposing_secret(self) -> None:
        with TemporaryDirectory() as tmp:
            store = MemorySecretStore()
            manager = ProviderManager(Path(tmp), "owner", secret_store=store)
            manager.configure(base_url="https://api.openai.com/v1", model="gpt-5-mini", api_key="test-secret")
            provider = manager.provider()
            self.assertIsNotNone(provider)
            assert provider is not None
            self.assertEqual(provider.base_url, "https://api.openai.com/v1")
            self.assertEqual(provider.model, "gpt-5-mini")
            status = manager.safe_status()
            self.assertFalse(status["secret_exposed"])
            self.assertNotIn("test-secret", str(status))


if __name__ == "__main__":
    unittest.main()
