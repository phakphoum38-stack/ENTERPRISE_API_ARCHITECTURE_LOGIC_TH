from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Provider(Protocol):
    name: str

    def complete(self, *, prompt: str, context: tuple[str, ...]) -> str: ...


@dataclass
class MockProvider:
    name: str = "owner-mock"

    def complete(self, *, prompt: str, context: tuple[str, ...]) -> str:
        prefix = f"context={len(context)}"
        return f"[{self.name} {prefix}] {prompt}"


class ProviderRouter:
    def __init__(self) -> None:
        self._providers: list[Provider] = []

    def register(self, provider: Provider) -> None:
        if any(existing.name == provider.name for existing in self._providers):
            raise ValueError(f"duplicate provider: {provider.name}")
        self._providers.append(provider)

    def set_primary(self, provider: Provider) -> None:
        self._providers = [existing for existing in self._providers if existing.name != provider.name]
        self._providers.insert(0, provider)

    def remove(self, name: str) -> None:
        self._providers = [provider for provider in self._providers if provider.name != name]

    def primary(self) -> Provider:
        if not self._providers:
            raise RuntimeError("no provider configured")
        return self._providers[0]

    def complete(self, *, prompt: str, context: tuple[str, ...]) -> tuple[str, str]:
        if not self._providers:
            raise RuntimeError("no provider configured")
        errors: list[str] = []
        for provider in self._providers:
            try:
                return provider.name, provider.complete(prompt=prompt, context=context)
            except Exception as exc:
                errors.append(f"{provider.name}:{type(exc).__name__}")
        raise RuntimeError("all providers failed: " + ",".join(errors))

    def names(self) -> tuple[str, ...]:
        return tuple(provider.name for provider in self._providers)
