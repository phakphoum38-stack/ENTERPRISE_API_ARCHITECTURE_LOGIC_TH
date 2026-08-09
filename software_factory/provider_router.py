from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ProviderCapability:
    provider: str
    capabilities: frozenset[str]
    priority: int = 100
    enabled: bool = True


@dataclass
class AgentProviderRouter:
    """Capability-first provider selection without hard-coding one AI vendor."""

    _providers: dict[str, ProviderCapability] = field(default_factory=dict)

    def register(self, capability: ProviderCapability) -> None:
        self._providers[capability.provider] = capability

    def disable(self, provider: str) -> None:
        current = self._providers[provider]
        self._providers[provider] = ProviderCapability(
            provider=current.provider,
            capabilities=current.capabilities,
            priority=current.priority,
            enabled=False,
        )

    def route(self, required: set[str]) -> str:
        candidates = [
            provider
            for provider in self._providers.values()
            if provider.enabled and required.issubset(provider.capabilities)
        ]
        if not candidates:
            raise LookupError(f"no enabled provider satisfies capabilities: {sorted(required)}")
        return min(candidates, key=lambda item: (item.priority, item.provider)).provider
