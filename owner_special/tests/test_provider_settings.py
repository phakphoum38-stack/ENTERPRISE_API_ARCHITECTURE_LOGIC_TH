import tempfile
import unittest
from pathlib import Path

from research_os_friend import MemorySecretStore, ProviderManager


class FakeTransport:
    def get_json(self, url, *, headers, timeout):
        assert headers["Authorization"] == "Bearer ci-provider-key"
        return {"data": [{"id": "mock-model"}]}

    def post_json(self, url, *, headers, payload, timeout):
        assert headers["Authorization"] == "Bearer ci-provider-key"
        assert payload["model"] == "mock-model"
        return {"choices": [{"message": {"content": "provider-ok"}}]}


class ProviderSettingsTests(unittest.TestCase):
    def test_configuration_never_exposes_key(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            manager = ProviderManager(Path(temporary), "owner", secret_store=MemorySecretStore(), transport=FakeTransport())
            status = manager.configure(base_url="http://127.0.0.1:9999/v1", model="mock-model", api_key="ci-provider-key")
            self.assertTrue(status["credential_present"])
            self.assertFalse(status["secret_exposed"])
            self.assertNotIn("ci-provider-key", str(status))
            self.assertTrue(manager.test()["connected"])
            provider = manager.provider()
            self.assertIsNotNone(provider)
            self.assertEqual(provider.complete(prompt="hello", context=()), "provider-ok")


if __name__ == "__main__":
    unittest.main()
