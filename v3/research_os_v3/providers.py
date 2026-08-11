from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .resilience import (
    CircuitBreakerPolicy,
    CircuitOpenError,
    ProviderUnavailableError,
    ResilientInvoker,
    RetryPolicy,
)
from .secrets import SecretSource, default_secret_source
from .transport import JsonTransport, UrllibJsonTransport


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    ready: bool
    connected: bool
    secret_exposed: bool = False
    metadata: dict[str, object] = field(default_factory=dict)

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "ready": self.ready,
            "connected": self.connected,
            "secret_exposed": False,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class CompletionRequest:
    prompt: str
    system_prompt: str | None = None


@dataclass(frozen=True)
class CompletionResponse:
    provider: str
    model: str
    text: str


class ProviderAdapter:
    name: str

    def status(self) -> ProviderStatus:
        raise NotImplementedError

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        raise NotImplementedError


class MockProvider(ProviderAdapter):
    name = "mock"

    def status(self) -> ProviderStatus:
        return ProviderStatus(name=self.name, ready=True, connected=True)

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(provider=self.name, model="mock", text=f"mock:{request.prompt}")


class OpenAICompatibleProvider(ProviderAdapter):
    name = "openai-compatible"

    def __init__(
        self,
        *,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-5",
        api_key_env: str = "OPENAI_API_KEY",
        secret_source: SecretSource | None = None,
        transport: JsonTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        if timeout <= 0:
            raise ValueError("provider timeout must be positive")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.secret_source = secret_source or default_secret_source()
        self.transport = transport or UrllibJsonTransport()
        self.timeout = timeout
        self._connected = False

    def status(self) -> ProviderStatus:
        try:
            credential_available = bool(self.secret_source.get(self.api_key_env))
        except Exception:
            credential_available = False
        return ProviderStatus(
            name=self.name,
            ready=credential_available and bool(self.base_url) and bool(self.model),
            connected=self._connected,
            secret_exposed=False,
            metadata={
                "base_url": self.base_url,
                "model": self.model,
                "credential_source": self.api_key_env,
                "credential_reference": self.api_key_env,
                "credential_available": credential_available,
                "secret_store_policy": "environment-then-os-native",
                "timeout_seconds": self.timeout,
            },
        )

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        api_key = self.secret_source.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"missing provider credential: {self.api_key_env}")

        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = self.transport.post_json(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            payload={"model": self.model, "messages": messages},
            timeout=self.timeout,
        )
        try:
            choices = payload["choices"]
            first = choices[0]  # type: ignore[index]
            message = first["message"]  # type: ignore[index]
            text = message["content"]  # type: ignore[index]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("provider response missing choices[0].message.content") from exc
        if not isinstance(text, str):
            raise RuntimeError("provider completion content is not text")

        self._connected = True
        return CompletionResponse(provider=self.name, model=self.model, text=text)


class ProviderRegistry:
    def __init__(
        self,
        providers: list[ProviderAdapter] | None = None,
        *,
        retry_policy: RetryPolicy | None = None,
        circuit_policy: CircuitBreakerPolicy | None = None,
        sleeper: Callable[[float], None] | None = None,
        clock: Callable[[], float] | None = None,
    ) -> None:
        self._providers = providers or [MockProvider()]
        names = [provider.name for provider in self._providers]
        if len(names) != len(set(names)):
            raise ValueError("provider names must be unique")

        invoker_kwargs: dict[str, object] = {
            "retry_policy": retry_policy,
            "circuit_policy": circuit_policy,
        }
        if sleeper is not None:
            invoker_kwargs["sleeper"] = sleeper
        if clock is not None:
            invoker_kwargs["clock"] = clock
        self._invokers = {
            provider.name: ResilientInvoker(**invoker_kwargs)  # type: ignore[arg-type]
            for provider in self._providers
        }

    def _status_for(self, provider: ProviderAdapter) -> ProviderStatus:
        status = provider.status()
        invoker = self._invokers[provider.name]
        circuit_state = invoker.circuit_state
        metadata = dict(status.metadata)
        metadata["resilience"] = {
            "circuit_state": circuit_state,
            "failure_count": invoker.breaker.failures,
            "max_attempts": invoker.retry_policy.max_attempts,
        }
        return ProviderStatus(
            name=status.name,
            ready=status.ready and circuit_state != "open",
            connected=status.connected,
            secret_exposed=False,
            metadata=metadata,
        )

    def statuses(self) -> list[ProviderStatus]:
        return [self._status_for(provider) for provider in self._providers]

    def select_ready(self) -> ProviderStatus:
        for provider in self._providers:
            status = self._status_for(provider)
            if status.ready:
                return status
        raise RuntimeError("no ready provider")

    def complete(
        self,
        request: CompletionRequest,
        *,
        preferred: str | None = None,
    ) -> CompletionResponse:
        ordered = list(self._providers)
        if preferred is not None:
            preferred_provider = next(
                (provider for provider in ordered if provider.name == preferred),
                None,
            )
            if preferred_provider is None:
                raise KeyError(preferred)
            ordered.remove(preferred_provider)
            ordered.insert(0, preferred_provider)

        attempted: list[str] = []
        for provider in ordered:
            status = self._status_for(provider)
            if not status.ready:
                continue
            attempted.append(provider.name)
            try:
                return self._invokers[provider.name].invoke(
                    lambda provider=provider: provider.complete(request)
                )
            except (ProviderUnavailableError, CircuitOpenError):
                continue

        attempted_text = ",".join(attempted) if attempted else "none"
        raise RuntimeError(f"no provider completed request; attempted={attempted_text}")

    def get(self, name: str) -> ProviderAdapter:
        for provider in self._providers:
            if provider.name == name:
                return provider
        raise KeyError(name)
