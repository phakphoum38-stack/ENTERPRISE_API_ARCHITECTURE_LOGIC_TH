from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

try:
    from .resource_governance import Usage
except ImportError:
    from resource_governance import Usage


@dataclass(frozen=True)
class ProviderMeasurement:
    """Authoritative accounting facts reported by the execution provider."""

    usage: Usage
    cost: Decimal | None = None
    currency: str | None = None

    def __post_init__(self) -> None:
        if self.cost is not None and self.cost < 0:
            raise ValueError("provider cost cannot be negative")

        normalized = self.currency.strip().upper() if self.currency is not None else None
        if self.cost is not None and not normalized:
            raise ValueError("provider currency is required when cost is present")
        if self.cost is None and normalized is not None:
            raise ValueError("provider currency requires provider cost")

        object.__setattr__(self, "currency", normalized)

    def to_measured_execution(
        self,
        value: object,
        *,
        required_currency: str,
    ):
        """Convert only complete authoritative accounting into MeasuredExecution."""
        try:
            from .execution_contract import MeasuredExecution
        except ImportError:
            from execution_contract import MeasuredExecution

        if self.cost is None or self.currency is None:
            raise ValueError("authoritative provider cost is required")

        expected = required_currency.strip().upper()
        if not expected:
            raise ValueError("required currency is required")
        if self.currency != expected:
            raise ValueError(
                f"provider currency mismatch: {self.currency} != {expected}"
            )

        return MeasuredExecution(
            value=value,
            usage=self.usage,
            cost=self.cost,
            currency=self.currency,
        )
