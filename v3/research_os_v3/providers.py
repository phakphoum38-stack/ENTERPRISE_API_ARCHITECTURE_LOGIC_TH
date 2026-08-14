from __future__ import annotations

import os
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
                "api_style": "chat-completions-compatible",
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


class GeminiProvider(ProviderAdapter):
    name = "gemini"

    def __init__(
        self,
        *,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        model: str = "gemini-3.6-flash",
        api_key_env: str = "GEMINI_API_KEY",
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
                "api_style": "generate-content",
            },
        )

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        api_key = self.secret_source.get(self.api_key_env)
        if not api_key:
            raise RuntimeError(f"missing provider credential: {self.api_key_env}")

        text = request.prompt
        if request.system_prompt:
            text = f"{request.system_prompt}\n\nUser request:\n{request.prompt}"
        payload = self.transport.post_json(
            f"{self.base_url}/models/{self.model}:generateContent",
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            payload={
                "contents": [
                    {
                        "role": "user",
                        "parts": [{"text": text}],
                    }
                ]
            },
            timeout=self.timeout,
        )
        try:
            candidates = payload["candidates"]
            first = candidates[0]  # type: ignore[index]
            content = first["content"]  # type: ignore[index]
            parts = content["parts"]  # type: ignore[index]
            fragments = [
                part.get("text", "")
                for part in parts  # type: ignore[union-attr]
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Gemini response missing candidates[0].content.parts") from exc
        response_text = "".join(fragments).strip()
        if not response_text:
            raise RuntimeError("Gemini completion content is empty")

        self._connected = True
        return CompletionResponse(provider=self.name, model=self.model, text=response_text)


_PROVIDER_ALIASES = {
    "openai": "openai-compatible",
    "local": "openai-compatible",
}


def _normalized_provider_name(name: str) -> str:
    normalized = name.strip().lower()
    return _PROVIDER_ALIASES.get(normalized, normalized)


def _first_available_secret_name(source: SecretSource, *names: str) -> str | None:
    for name in names:
        try:
            if source.get(name):
                return name
        except Exception:
            continue
    return None


def _env(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else default


def runtime_provider_registry(
    *,
    secret_source: SecretSource | None = None,
    transport: JsonTransport | None = None,
) -> "ProviderRegistry":
    """Build the runtime registry without embedding credentials in source.

    ``RESEARCH_OS_PROVIDER=auto`` registers every provider whose credential can
    be resolved from the process environment or OS-native secret store. Mock is
    used only when auto mode finds no usable real-provider credential.
    Explicit provider selection keeps that provider visible even when its
    credential is missing, so readiness failures are observable instead of
    silently pretending a mock response is real.
    """

    source = secret_source or default_secret_source()
    selected = _normalized_provider_name(_env("RESEARCH_OS_PROVIDER", "auto"))
    providers: list[ProviderAdapter] = []

    openai_key_name = _first_available_secret_name(
        source,
        "RESEARCH_OS_OPENAI_API_KEY",
        "OPENAI_API_KEY",
    )
    gemini_key_name = _first_available_secret_name(
        source,
        "RESEARCH_OS_GEMINI_API_KEY",
        "GEMINI_API_KEY",
    )

    def openai_provider(key_name: str) -> OpenAICompatibleProvider:
        return OpenAICompatibleProvider(
            base_url=_env("RESEARCH_OS_OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=_env("RESEARCH_OS_OPENAI_MODEL", "gpt-5"),
            api_key_env=key_name,
            secret_source=source,
            transport=transport,
            timeout=float(_env("RESEARCH_OS_PROVIDER_TIMEOUT", "30")),
        )

    def gemini_provider(key_name: str) -> GeminiProvider:
        return GeminiProvider(
            base_url=_env(
                "RESEARCH_OS_GEMINI_BASE_URL",
                "https://generativelanguage.googleapis.com/v1beta",
            ),
            model=_env("RESEARCH_OS_GEMINI_MODEL", "gemini-3.6-flash"),
            api_key_env=key_name,
            secret_source=source,
            transport=transport,
            timeout=float(_env("RESEARCH_OS_PROVIDER_TIMEOUT", "30")),
        )

    if selected == "auto":
        order = [
            _normalized_provider_name(item)
            for item in _env(
                "RESEARCH_OS_PROVIDER_ORDER",
                "openai-compatible,gemini",
            ).split(",")
            if item.strip()
        ]
        for name in order:
            if name == "openai-compatible" and openai_key_name and not any(
                provider.name == "openai-compatible" for provider in providers
            ):
                providers.append(openai_provider(openai_key_name))
            elif name == "gemini" and gemini_key_name and not any(
                provider.name == "gemini" for provider in providers
            ):
                providers.append(gemini_provider(gemini_key_name))
        if not providers:
            providers.append(MockProvider())
    elif selected == "openai-compatible":
        providers.append(openai_provider(openai_key_name or "RESEARCH_OS_OPENAI_API_KEY"))
    elif selected == "gemini":
        providers.append(gemini_provider(gemini_key_name or "RESEARCH_OS_GEMINI_API_KEY"))
    elif selected == "mock":
        providers.append(MockProvider())
    else:
        raise ValueError(f"unsupported RESEARCH_OS_PROVIDER: {selected}")

    return ProviderRegistry(providers)


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
            preferred = _normalized_provider_name(preferred)
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
        wanted = _normalized_provider_name(name)
        for provider in self._providers:
            if provider.name == wanted:
                return provider
        raise KeyError(wanted)
