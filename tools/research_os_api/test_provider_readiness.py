import json
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
        self.assertIn("OPENAI_API_KEY", status["missing"])

    def test_openai_compatible_ready_with_standard_key_alias(self):
        env = {
            "OPENAI_API_KEY": "test-standard-key",
            "RESEARCH_OS_OPENAI_ENDPOINT": "https://api.openai.com/v1/chat/completions",
            "RESEARCH_OS_OPENAI_MODEL": "gpt-test",
        }
        with patch.dict(os.environ, env, clear=True):
            status = provider_readiness.inspect_provider("openai-compatible")
        self.assertTrue(status["ready"])
        self.assertEqual([], status["missing"])
        self.assertNotIn("test-standard-key", json.dumps(status))

    def test_openai_responses_ready_with_existing_standard_key(self):
        with patch.dict(
            os.environ,
            {"OPENAI_API_KEY": "test-existing-key"},
            clear=True,
        ):
            status = provider_readiness.inspect_provider("openai-responses")
        self.assertTrue(status["ready"])
        self.assertTrue(status["endpoint_configured"])
        self.assertTrue(status["model_configured"])
        self.assertNotIn("test-existing-key", json.dumps(status))

    def test_openai_search_alias_is_canonicalized(self):
        with patch.dict(
            os.environ,
            {
                "RESEARCH_OS_PROVIDER": "openai-search",
                "RESEARCH_OS_OPENAI_API_KEY": "test-key",
            },
            clear=True,
        ):
            report = provider_readiness.inspect_all()
        self.assertEqual("openai-responses", report["active"])
        active = next(
            item for item in report["providers"] if item["provider"] == report["active"]
        )
        self.assertTrue(active["ready"])

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
