from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from resource_governance import Usage


@dataclass(frozen=True)
class MeasuredExecution:
    """Execution output plus authoritative measured accounting values."""

    value: Any
    usage: Usage
    cost: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError("execution cost cannot be negative")
        currency = self.currency.strip().upper()
        if not currency:
            raise ValueError("execution currency is required")
        object.__setattr__(self, "currency", currency)


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable context passed from the control plane into an executor."""

    request_id: str
    principal_id: str
    provider: str
    model: str
    route: dict[str, Any]

    def __post_init__(self) -> None:
        for field_name in (
            "request_id",
            "principal_id",
            "provider",
            "model",
        ):
            if not getattr(self, field_name).strip():
                raise ValueError(f"{field_name} is required")
