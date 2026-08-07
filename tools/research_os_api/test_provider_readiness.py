import os
import unittest
from unittest.mock import patch

import provider_readiness


class ProviderReadinessTests(unittest.TestCase):
    def test_mock_is_always_ready(self):
        with patch.dict(os.environ, {}, clear=True):
            status = provider_readiness.inspect_provider("mock")
        self.assertTrue(status["ready"])
        self.assertEqual([], status["missing"])

    def test_anthropic_reports_missing_without_secret_values(self):
        with patch.dict(os.environ, {}, clear=True):
            status = provider_readiness.inspect_provider("anthropic")
        self.assertFalse(status["ready"])
        self.assertIn("RESEARCH_OS_ANTHROPIC_API_KEY", status["missing"])
        self.assertNotIn("api_key", status)

    def test_openai_compatible_requires_api_key(self):
        env = {
            "RESEARCH_OS_OPENAI_ENDPOINT": "https://api.openai.com/v1/chat/completions",
            "RESEARCH_OS_OPENAI_MODEL": "gpt-test",
        }
        with patch.dict(os.environ, env, clear=True):
            status = provider_readiness.inspect_provider("openai-compatible")
        self.assertFalse(status["ready"])
        self.assertIn("RESEARCH_OS_OPENAI_API_KEY", status["missing"])

    def test_openai_compatible_ready_with_key_endpoint_and_model(self):
        env = {
            "RESEARCH_OS_OPENAI_API_KEY": "test-key",
            "RESEARCH_OS_OPENAI_ENDPOINT": "https://api.openai.com/v1/chat/completions",
            "RESEARCH_OS_OPENAI_MODEL": "gpt-test",
        }
        with patch.dict(os.environ, env, clear=True):
            status = provider_readiness.inspect_provider("openai-compatible")
        self.assertTrue(status["ready"])
        self.assertEqual([], status["missing"])

    def test_local_ready_without_api_key(self):
        env = {
            "RESEARCH_OS_OPENAI_ENDPOINT": "http://localhost:11434/v1/chat/completions",
            "RESEARCH_OS_OPENAI_MODEL": "local-model",
        }
        with patch.dict(os.environ, env, clear=True):
            status = provider_readiness.inspect_provider("local")
        self.assertTrue(status["ready"])


if __name__ == "__main__":
    unittest.main()
