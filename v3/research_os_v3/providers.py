from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .secrets import EnvironmentSecretSource, SecretSource
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


class ProviderAdapter(Protocol):
    name: str

    def status(self) -> ProviderStatus: ...

    def complete(self, request: CompletionRequest) -> CompletionResponse: ...


class MockProvider:
    name = "mock"

    def status(self) -> ProviderStatus:
        return ProviderStatus(name=self.name, ready=True, connected=True)

    def complete(self, request: CompletionRequest) -> CompletionResponse:
        return CompletionResponse(provider=self.name, model="mock", text=f"mock:{request.prompt}")


class OpenAICompatibleProvider:
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
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key_env = api_key_env
        self.secret_source = secret_source or EnvironmentSecretSource()
        self.transport = transport or UrllibJsonTransport()
        self.timeout = timeout
        self._connected = False

    def status(self) -> ProviderStatus:
        credential_available = bool(self.secret_source.get(self.api_key_env))
        return ProviderStatus(
            name=self.name,
            ready=credential_available and bool(self.base_url) and bool(self.model),
            connected=self._connected,
            secret_exposed=False,
            metadata={
                "base_url": self.base_url,
                "model": self.model,
                "credential_source": self.api_key_env,
                "credential_available": credential_available,
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
    def __init__(self, providers: list[ProviderAdapter] | None = None) -> None:
        self._providers = providers or [MockProvider()]

    def statuses(self) -> list[ProviderStatus]:
        return [provider.status() for provider in self._providers]

    def select_ready(self) -> ProviderStatus:
        for status in self.statuses():
            if status.ready:
                return status
        raise RuntimeError("no ready provider")

    def get(self, name: str) -> ProviderAdapter:
        for provider in self._providers:
            if provider.name == name:
                return provider
        raise KeyError(name)
