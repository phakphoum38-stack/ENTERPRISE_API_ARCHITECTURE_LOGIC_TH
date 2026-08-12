from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from research_os_v3 import (
    CircuitBreakerPolicy,
    CompletionRequest,
    CompletionResponse,
    MockProvider,
    ProviderRegistry,
    ProviderStatus,
    RetryPolicy,
    WindowsCredentialManagerSecretSource,
)


class FlakyProvider:
    name = "flaky-smoke"

    def __init__(self, failures_before_success: int) -> None:
        self.failures_before_success = failures_before_success
        self.calls = 0

    def status(self) -> ProviderStatus:
        return ProviderStatus(name=self.name, ready=True, connected=self.calls > 0)

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        self.calls += 1
        if self.calls <= self.failures_before_success:
            raise TimeoutError("simulated timeout")
        return CompletionResponse(provider=self.name, model="smoke", text="ok")


def main() -> int:
    targets: list[str] = []
    native = WindowsCredentialManagerSecretSource(
        reader=lambda target: targets.append(target) or "synthetic-secret"
    )
    assert native.get("OPENAI_API_KEY") == "synthetic-secret"
    assert targets == ["ResearchOSV3/OPENAI_API_KEY"]

    retry_provider = FlakyProvider(failures_before_success=1)
    retry_registry = ProviderRegistry(
        [retry_provider, MockProvider()],
        retry_policy=RetryPolicy(max_attempts=2, initial_backoff_seconds=0),
        circuit_policy=CircuitBreakerPolicy(failure_threshold=2, recovery_timeout_seconds=60),
        sleeper=lambda _: None,
    )
    retried = retry_registry.complete(
        CompletionRequest(prompt="retry-smoke"), preferred="flaky-smoke"
    )
    assert retried.provider == "flaky-smoke"
    assert retry_provider.calls == 2

    failing_provider = FlakyProvider(failures_before_success=100)
    fallback_registry = ProviderRegistry(
        [failing_provider, MockProvider()],
        retry_policy=RetryPolicy(max_attempts=2, initial_backoff_seconds=0),
        circuit_policy=CircuitBreakerPolicy(failure_threshold=1, recovery_timeout_seconds=60),
        sleeper=lambda _: None,
    )
    fallback = fallback_registry.complete(
        CompletionRequest(prompt="fallback-smoke"), preferred="flaky-smoke"
    )
    assert fallback.provider == "mock"
    status = next(item for item in fallback_registry.statuses() if item.name == "flaky-smoke")
    assert status.metadata["resilience"]["circuit_state"] == "open"
    assert status.secret_exposed is False

    output = {
        "os_native_secret_target": targets[0],
        "retry_attempts_observed": retry_provider.calls,
        "fallback_provider": fallback.provider,
        "circuit_state": status.metadata["resilience"]["circuit_state"],
        "secret_exposed": False,
    }
    serialized = json.dumps(output, sort_keys=True)
    assert "synthetic-secret" not in serialized
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
