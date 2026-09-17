from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Protocol

from provider_measurement import ProviderMeasurement
from resource_governance import Usage


@dataclass(frozen=True)
class ProviderResult:
    """Provider output with authoritative measurement metadata."""

    text: str
    usage: dict[str, int] = field(default_factory=dict)
    actual_cost: Decimal | None = None
    currency: str = "USD"
    raw: dict[str, Any] = field(default_factory=dict)
    measurement: ProviderMeasurement | None = None

    def __post_init__(self) -> None:
        measurement = self.measurement
        if measurement is None:
            requests = int(self.usage.get("requests", 0))
            tokens = int(self.usage.get("tokens", 0))
            measurement = ProviderMeasurement(
                usage=Usage(requests=requests, tokens=tokens),
                cost=self.actual_cost,
                currency=self.currency if self.actual_cost is not None else None,
            )
            object.__setattr__(self, "measurement", measurement)


class Provider(Protocol):
    name: str

    def complete(self, *, prompt: str, context: tuple[str, ...]) -> ProviderResult: ...


@dataclass
class MockProvider:
    name: str = "owner-mock"

    def complete(self, *, prompt: str, context: tuple[str, ...]) -> ProviderResult:
        prefix = f"context={len(context)}"
        return ProviderResult(
            text=f"[{self.name} {prefix}] {prompt}",
            usage={"requests": 1},
            actual_cost=Decimal("0"),
            currency="USD",
            raw={"mock": True},
        )


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

    def complete(self, *, prompt: str, context: tuple[str, ...]) -> tuple[str, ProviderResult]:
        if not self._providers:
            raise RuntimeError("no provider configured")
        errors: list[str] = []
        for provider in self._providers:
            try:
                result = provider.complete(prompt=prompt, context=context)
                if isinstance(result, ProviderResult):
                    return provider.name, result
                raise TypeError("provider must return ProviderResult with authoritative measurement")
            except Exception as exc:
                errors.append(f"{provider.name}:{type(exc).__name__}")
        raise RuntimeError("all providers failed: " + ",".join(errors))

    def names(self) -> tuple[str, ...]:
        return tuple(provider.name for provider in self._providers)
