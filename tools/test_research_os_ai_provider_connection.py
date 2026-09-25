import os
import unittest
from unittest.mock import patch

from tools.research_os_ai_provider_connection import (
    _configured,
    connect,
    inspect,
)


class AIProviderConnectionTests(unittest.TestCase):
    def test_openai_not_connected_is_secret_safe(self):
        with patch.dict(os.environ, {}, clear=True):
            item = _configured("openai")
        self.assertEqual(item.state, "NOT_CONNECTED")
        self.assertFalse(item.secret_exposed)
        self.assertTrue(item.api_fallback_available)

    def test_gemini_connected_when_secret_and_model_exist(self):
        with patch.dict(
            os.environ,
            {
                "RESEARCH_OS_GEMINI_API_KEY": "secret",
                "RESEARCH_OS_GEMINI_MODEL": "gemini-test",
            },
            clear=True,
        ):
            item = _configured("gemini")
        self.assertEqual(item.state, "CONNECTED")
        self.assertFalse(item.secret_exposed)

    def test_connect_is_backend_readiness_only(self):
        with patch.dict(
            os.environ,
            {
                "RESEARCH_OS_OPENAI_API_KEY": "TOP-SECRET",
                "RESEARCH_OS_OPENAI_MODEL": "gpt-test",
                "RESEARCH_OS_SOURCE_SHA": "abc123",
            },
            clear=True,
        ):
            result = connect("openai")
        self.assertEqual(result["connection"]["operation"], "CONNECT")
        self.assertEqual(result["connection"]["state"], "CONNECTED")
        self.assertFalse(result["connection"]["secret_exposed"])
        self.assertEqual(result["evidence"]["source_sha"], "abc123")
        self.assertIn("timestamp", result["evidence"])
        self.assertNotIn("TOP-SECRET", str(result))

    def test_inspect_never_contains_secret(self):
        with patch.dict(
            os.environ,
            {
                "RESEARCH_OS_OPENAI_API_KEY": "TOP-SECRET",
                "RESEARCH_OS_OPENAI_MODEL": "gpt-test",
            },
            clear=True,
        ):
            report = inspect()
        self.assertNotIn("TOP-SECRET", str(report))
        self.assertTrue(report["safe"])


if __name__ == "__main__":
    unittest.main()
