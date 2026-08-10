from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    ready: bool
    connected: bool
    secret_exposed: bool = False

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "ready": self.ready,
            "connected": self.connected,
            "secret_exposed": False,
        }


class ProviderAdapter(Protocol):
    name: str

    def status(self) -> ProviderStatus: ...


class MockProvider:
    name = "mock"

    def status(self) -> ProviderStatus:
        return ProviderStatus(name=self.name, ready=True, connected=True)


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
