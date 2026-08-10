#!/usr/bin/env python3
from __future__ import annotations

import json
import unittest
from unittest.mock import patch

import service_provider_smoke


class ServiceProviderSmokeTests(unittest.TestCase):
    def test_openai_service_smoke_runs_generate_and_search_without_returning_content(self) -> None:
        responses = [
            (200, {"status": "ok"}),
            (
                200,
                {
                    "api_version": "v2",
                    "providers": {
                        "openai-responses": {
                            "configured": True,
                            "credential_source": "OPENAI_API_KEY",
                            "secret_exposed": False,
                            "supports_web_search": True,
                        },
                        "gemini": {
                            "configured": False,
                            "secret_exposed": False,
                            "supports_web_search": False,
                        },
                    },
                },
            ),
            (200, {"provider": "openai-responses", "text": "READY"}),
            (
                200,
                {
                    "result": {
                        "text": "sourced answer",
                        "sources": [{"url": "https://example.com", "title": "Evidence"}],
                    }
                },
            ),
        ]
        with patch("service_provider_smoke._request_json", side_effect=responses):
            code, report = service_provider_smoke.run("http://127.0.0.1:8787")

        self.assertEqual(code, 0)
        self.assertTrue(report["health_ok"])
        self.assertTrue(report["generate_connected"])
        self.assertTrue(report["web_search_connected"])
        self.assertTrue(report["web_search_sources_received"])
        serialized = json.dumps(report)
        self.assertNotIn("READY", serialized)
        self.assertNotIn("sourced answer", serialized)
        self.assertNotIn("https://example.com", serialized)
        self.assertTrue(report["secret_safe"])

    def test_non_search_provider_can_pass_generation_without_claiming_web_search(self) -> None:
        responses = [
            (200, {"status": "ok"}),
            (
                200,
                {
                    "providers": {
                        "openai-responses": {
                            "configured": False,
                            "secret_exposed": False,
                            "supports_web_search": True,
                        },
                        "gemini": {
                            "configured": True,
                            "credential_source": "GEMINI_API_KEY",
                            "secret_exposed": False,
                            "supports_web_search": False,
                        },
                    }
                },
            ),
            (200, {"provider": "gemini", "text": "READY"}),
        ]
        with patch("service_provider_smoke._request_json", side_effect=responses):
            code, report = service_provider_smoke.run()

        self.assertEqual(code, 0)
        self.assertEqual(report["selected_provider"], "gemini")
        self.assertTrue(report["generate_response_received"])
        self.assertFalse(report["web_search_supported"])
        self.assertFalse(report["web_search_attempted"])

    def test_missing_real_provider_fails_before_generation(self) -> None:
        responses = [
            (200, {"status": "ok"}),
            (
                200,
                {
                    "providers": {
                        "openai-responses": {
                            "configured": False,
                            "secret_exposed": False,
                            "supports_web_search": True,
                        },
                        "gemini": {
                            "configured": False,
                            "secret_exposed": False,
                            "supports_web_search": False,
                        },
                        "anthropic": {
                            "configured": False,
                            "secret_exposed": False,
                            "supports_web_search": False,
                        },
                    }
                },
            ),
        ]
        with patch("service_provider_smoke._request_json", side_effect=responses):
            code, report = service_provider_smoke.run()

        self.assertEqual(code, 2)
        self.assertEqual(report["failure_stage"], "real_provider_not_configured")
        self.assertFalse(report["generate_attempted"])

    def test_provider_error_detail_is_never_copied_to_report(self) -> None:
        fake_secret = "sk-never-print-this-secret-123456789"
        responses = [
            (200, {"status": "ok"}),
            (
                200,
                {
                    "providers": {
                        "openai-responses": {
                            "configured": True,
                            "secret_exposed": False,
                            "supports_web_search": True,
                        }
                    }
                },
            ),
            (
                502,
                {
                    "error": "provider_error",
                    "detail": f"remote body accidentally contained {fake_secret}",
                },
            ),
        ]
        with patch("service_provider_smoke._request_json", side_effect=responses):
            code, report = service_provider_smoke.run()

        self.assertEqual(code, 1)
        self.assertEqual(report["failure_stage"], "generate")
        self.assertEqual(report["error_code"], "provider_error")
        self.assertNotIn(fake_secret, json.dumps(report))
        self.assertTrue(report["secret_safe"])


if __name__ == "__main__":
    unittest.main()
