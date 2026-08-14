from __future__ import annotations

import json
import os
import unittest
from unittest.mock import patch

from research_os_v3 import (
    CircuitBreakerPolicy,
    CompletionRequest,
    CompletionResponse,
    CompositeSecretSource,
    GeminiProvider,
    MockProvider,
    ProviderRegistry,
    ProviderStatus,
    RetryPolicy,
    WindowsCredentialManagerSecretSource,
    runtime_provider_registry,
)


class StaticSource:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def get(self, name: str) -> str | None:
        return self.values.get(name)


class FakeTransport:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    def post_json(
        self,
        url: str,
        *,
        headers: dict[str, str],
        payload: dict[str, object],
        timeout: float,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "url": url,
                "headers": dict(headers),
                "payload": payload,
                "timeout": timeout,
            }
        )
        return self.response


class FlakyProvider:
    name = "flaky"

    def __init__(self, failures_before_success: int) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    def status(self) -> ProviderStatus:
        return ProviderStatus(name=self.name, ready=True, connected=self.calls > 0)

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise TimeoutError("simulated provider timeout")
        return CompletionResponse(provider=self.name, model="fake", text=f"ok:{request.prompt}")


class ProviderResilienceTests(unittest.TestCase):
    def test_windows_credential_manager_source_uses_namespaced_target(self) -> None:
        calls: list[str] = []

        def reader(target: str) -> str | None:
            calls.append(target)
            return "native-secret"

        source = WindowsCredentialManagerSecretSource(reader=reader)
        self.assertEqual(source.get("OPENAI_API_KEY"), "native-secret")
        self.assertEqual(calls, ["ResearchOSV3/OPENAI_API_KEY"])

    def test_windows_credential_manager_missing_target_is_safe(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows Credential Manager is Windows-only")
        source = WindowsCredentialManagerSecretSource(
            target_prefix="ResearchOSV3-CI-Definitely-Missing/"
        )
        self.assertIsNone(source.get("OPENAI_API_KEY"))

    def test_composite_source_falls_back_without_exposing_values(self) -> None:
        source = CompositeSecretSource(
            (StaticSource({}), StaticSource({"OPENAI_API_KEY": "fallback-secret"}))
        )
        self.assertEqual(source.get("OPENAI_API_KEY"), "fallback-secret")
        self.assertIsNone(source.get("OTHER"))

    def test_gemini_uses_header_credential_and_never_places_key_in_url(self) -> None:
        secret = "gemini-secret"
        transport = FakeTransport(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [{"text": "gemini-ok"}],
                        }
                    }
                ]
            }
        )
        provider = GeminiProvider(
            secret_source=StaticSource({"GEMINI_API_KEY": secret}),
            transport=transport,
            model="gemini-test",
        )

        response = provider.complete(CompletionRequest(prompt="hello"))
        self.assertEqual(response.text, "gemini-ok")
        self.assertEqual(response.provider, "gemini")
        self.assertEqual(len(transport.calls), 1)
        call = transport.calls[0]
        self.assertEqual(
            call["url"],
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-test:generateContent",
        )
        self.assertEqual(call["headers"]["x-goog-api-key"], secret)
        self.assertNotIn(secret, str(call["url"]))
        self.assertNotIn(secret, json.dumps(provider.status().to_safe_dict(), sort_keys=True))

    def test_runtime_auto_uses_gemini_when_only_gemini_key_exists(self) -> None:
        source = StaticSource({"RESEARCH_OS_GEMINI_API_KEY": "gemini-secret"})
        with patch.dict(
            os.environ,
            {"RESEARCH_OS_PROVIDER": "auto"},
            clear=False,
        ):
            registry = runtime_provider_registry(secret_source=source)
        statuses = registry.statuses()
        self.assertEqual([item.name for item in statuses], ["gemini"])
        self.assertTrue(statuses[0].ready)
        self.assertFalse(statuses[0].secret_exposed)

    def test_runtime_auto_falls_back_to_mock_only_without_real_credentials(self) -> None:
        source = StaticSource({})
        with patch.dict(
            os.environ,
            {
                "RESEARCH_OS_PROVIDER": "auto",
                "RESEARCH_OS_PROVIDER_ORDER": "openai-compatible,gemini",
            },
            clear=False,
        ):
            registry = runtime_provider_registry(secret_source=source)
        statuses = registry.statuses()
        self.assertEqual([item.name for item in statuses], ["mock"])
        self.assertTrue(statuses[0].ready)

    def test_explicit_openai_without_key_does_not_silently_become_mock(self) -> None:
        source = StaticSource({})
        with patch.dict(
            os.environ,
            {"RESEARCH_OS_PROVIDER": "openai"},
            clear=False,
        ):
            registry = runtime_provider_registry(secret_source=source)
        statuses = registry.statuses()
        self.assertEqual([item.name for item in statuses], ["openai-compatible"])
        self.assertFalse(statuses[0].ready)

    def test_retry_policy_recovers_before_fallback(self) -> None:
        provider = FlakyProvider(failures_before_success=2)
        sleeps: list[float] = []
        registry = ProviderRegistry(
            [provider, MockProvider()],
            retry_policy=RetryPolicy(
                max_attempts=3,
                initial_backoff_seconds=0.01,
                max_backoff_seconds=0.02,
            ),
            circuit_policy=CircuitBreakerPolicy(
                failure_threshold=2,
                recovery_timeout_seconds=60.0,
            ),
            sleeper=sleeps.append,
        )

        response = registry.complete(CompletionRequest(prompt="retry"), preferred="flaky")
        self.assertEqual(response.provider, "flaky")
        self.assertEqual(provider.calls, 3)
        self.assertEqual(sleeps, [0.01, 0.02])
        status = next(item for item in registry.statuses() if item.name == "flaky")
        self.assertEqual(status.metadata["resilience"]["circuit_state"], "closed")

    def test_circuit_breaker_opens_and_registry_falls_back(self) -> None:
        provider = FlakyProvider(failures_before_success=100)
        registry = ProviderRegistry(
            [provider, MockProvider()],
            retry_policy=RetryPolicy(max_attempts=2, initial_backoff_seconds=0),
            circuit_policy=CircuitBreakerPolicy(
                failure_threshold=1,
                recovery_timeout_seconds=60.0,
            ),
            sleeper=lambda _: None,
        )

        first = registry.complete(CompletionRequest(prompt="fallback"), preferred="flaky")
        self.assertEqual(first.provider, "mock")
        self.assertEqual(provider.calls, 2)

        second = registry.complete(CompletionRequest(prompt="still-fallback"), preferred="flaky")
        self.assertEqual(second.provider, "mock")
        self.assertEqual(provider.calls, 2, "open circuit must prevent new provider calls")

        status = next(item for item in registry.statuses() if item.name == "flaky")
        self.assertFalse(status.ready)
        self.assertEqual(status.metadata["resilience"]["circuit_state"], "open")
        self.assertFalse(status.secret_exposed)


if __name__ == "__main__":
    unittest.main()
