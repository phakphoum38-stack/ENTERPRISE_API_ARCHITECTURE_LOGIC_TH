from __future__ import annotations

import os
import unittest

from research_os_v3 import (
    CircuitBreakerPolicy,
    CompletionRequest,
    CompletionResponse,
    CompositeSecretSource,
    MockProvider,
    ProviderRegistry,
    ProviderStatus,
    RetryPolicy,
    WindowsCredentialManagerSecretSource,
)


class StaticSource:
    def __init__(self, values: dict[str, str]) -> None:
        self.values = values

    def get(self, name: str) -> str | None:
        return self.values.get(name)


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
