"""Contract types shared by governed runtime execution surfaces.

This module contains no admission, routing, or provider logic. Runtime
surfaces must hand measured execution results back to ResourceControlPlane;
these types make that boundary explicit without introducing a second control
plane.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

try:
    from .resource_governance import Usage
except ImportError:
    # Existing resource-control modules historically use flat imports when
    # tools/research_os_api is placed directly on sys.path.
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
        if not self.currency.strip():
            raise ValueError("execution currency is required")
        object.__setattr__(self, "currency", self.currency.strip().upper())


@dataclass(frozen=True)
class ExecutionContext:
    """Immutable context passed from the control plane into an executor."""

    request_id: str
    principal_id: str
    provider: str
    model: str
    route: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.principal_id.strip():
            raise ValueError("principal_id is required")
        if not self.provider.strip():
            raise ValueError("provider is required")
        if not self.model.strip():
            raise ValueError("model is required")
