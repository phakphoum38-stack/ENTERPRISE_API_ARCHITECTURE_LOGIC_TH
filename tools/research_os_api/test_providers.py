import os
import unittest
from unittest.mock import patch

import providers
from providers import OpenAIResponsesProvider, ProviderError


class ProviderCredentialDiscoveryTests(unittest.TestCase):
    def test_existing_standard_openai_key_is_discovered_without_exposure(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-existing-key"}, clear=True):
            status = providers.provider_credential_status()
            self.assertTrue(status["openai-responses"]["configured"])
            self.assertEqual(
                status["openai-responses"]["credential_source"],
                "OPENAI_API_KEY",
            )
            self.assertFalse(status["openai-responses"]["secret_exposed"])
            self.assertNotIn("test-existing-key", repr(status))
            self.assertIsInstance(
                providers.build_search_provider(),
                OpenAIResponsesProvider,
            )

    def test_openai_responses_search_enables_web_search_and_collects_sources(self):
        raw = {
            "output": [
                {
                    "type": "web_search_call",
                    "action": {
                        "sources": [
                            {"url": "https://example.com/source", "title": "Evidence"}
                        ]
                    },
                },
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "A source-backed answer.",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "url": "https://example.com/source",
                                    "title": "Evidence",
                                }
                            ],
                        }
                    ],
                },
            ]
        }
        provider = OpenAIResponsesProvider(
            endpoint="https://api.openai.com/v1/responses",
            api_key="test-key",
            default_model="test-model",
        )
        with patch("providers._post_json", return_value=raw) as post:
            result = provider.search(
                "latest evidence",
                system="cite current sources",
            )

        payload = post.call_args.args[1]
        self.assertEqual(payload["tools"], [{"type": "web_search"}])
        self.assertEqual(payload["tool_choice"], "auto")
        self.assertFalse(payload["store"])
        self.assertEqual(result.text, "A source-backed answer.")
        self.assertEqual(len(result.sources), 1)
        self.assertEqual(result.sources[0]["url"], "https://example.com/source")

    def test_missing_key_fails_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ProviderError):
                providers.build_search_provider()


if __name__ == "__main__":
    unittest.main()
