#!/usr/bin/env python3
from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from ai_gateway import gateway_report, inspect_providers, resolve_provider


class AIGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.keys = (
            "RESEARCH_OS_PROVIDER",
            "RESEARCH_OS_ENABLE_LOCAL_PROVIDER_DISCOVERY",
            "RESEARCH_OS_OPENAI_ENDPOINT",
            "RESEARCH_OS_OPENAI_API_KEY",
            "OPENAI_API_KEY",
            "RESEARCH_OS_GEMINI_API_KEY",
            "GEMINI_API_KEY",
            "RESEARCH_OS_ANTHROPIC_API_KEY",
            "ANTHROPIC_API_KEY",
            "CI",
        )
        self.previous = {key: os.environ.get(key) for key in self.keys}
        for key in self.keys:
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        for key, value in self.previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_explicit_provider_always_wins(self) -> None:
        os.environ["RESEARCH_OS_PROVIDER"] = "gemini"
        resolution = resolve_provider(probe=lambda _: True)
        self.assertEqual("gemini", resolution.provider)
        self.assertEqual("explicit", resolution.source)

    def test_local_first_auto_resolution(self) -> None:
        os.environ["RESEARCH_OS_ENABLE_LOCAL_PROVIDER_DISCOVERY"] = "1"
        os.environ["GEMINI_API_KEY"] = "secret-value-that-must-not-leak"
        resolution = resolve_provider(probe=lambda _: True)
        self.assertEqual("local", resolution.provider)
        self.assertEqual("localhost-probe", resolution.source)

    def test_environment_credential_is_detected_without_value_leak(self) -> None:
        os.environ["GEMINI_API_KEY"] = "do-not-return-this"
        os.environ["CI"] = "true"
        report = gateway_report(probe=lambda _: self.fail("CI must not probe localhost"))
        self.assertEqual("gemini", report["selected"]["provider"])
        self.assertNotIn("do-not-return-this", repr(report))
        gemini = next(item for item in report["providers"] if item["provider"] == "gemini")
        self.assertTrue(gemini["credential_present"])
        self.assertTrue(gemini["ready"])

    def test_ci_skips_local_probe_and_falls_back_to_mock(self) -> None:
        os.environ["CI"] = "true"
        resolution = resolve_provider(probe=lambda _: self.fail("local probe must be skipped in CI"))
        self.assertEqual("mock", resolution.provider)
        self.assertEqual("builtin", resolution.source)

    def test_explicit_local_endpoint_is_ready_without_network_probe(self) -> None:
        os.environ["RESEARCH_OS_OPENAI_ENDPOINT"] = "http://localhost:1234/v1/chat/completions"
        statuses = inspect_providers(probe=lambda _: self.fail("explicit endpoint must not require discovery probe"))
        local = next(item for item in statuses if item.provider == "local")
        self.assertTrue(local.ready)
        self.assertEqual("environment", local.source)

    def test_auto_mode_can_be_explicitly_selected(self) -> None:
        os.environ["RESEARCH_OS_PROVIDER"] = "auto"
        os.environ["CI"] = "true"
        os.environ["ANTHROPIC_API_KEY"] = "configured"
        resolution = resolve_provider(probe=lambda _: False)
        self.assertEqual("anthropic", resolution.provider)


if __name__ == "__main__":
    unittest.main()
