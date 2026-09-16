"""Friend-to-Resource-Control-Plane execution boundary.

The Friend runtime remains the owner of Friend orchestration, Brain, skills,
and tools. This adapter owns only admission/execution normalization: Friend
execution must enter the canonical ResourceControlPlane and must return an
explicit MeasuredExecution before quota/budget commitment.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable

try:
    from .execution_contract import MeasuredExecution
    from .resource_control_plane import ExecutionResult, ResourceControlPlane
    from .resource_governance import Usage
except ImportError:
    from execution_contract import MeasuredExecution
    from resource_control_plane import ExecutionResult, ResourceControlPlane
    from resource_governance import Usage


@dataclass(frozen=True)
class FriendControlRequest:
    """Canonical resource inputs attached to one Friend execution."""

    request_id: str
    principal_id: str
    objective: str
    usage: Usage
    estimated_cost: Decimal
    currency: str
    scopes: frozenset[str]
    available_providers: tuple[str, ...] = ()
    requested_agent: str | None = None
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.principal_id.strip():
            raise ValueError("principal_id is required")
        if not self.objective.strip():
            raise ValueError("objective is required")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")


class FriendResourceControlAdapter:
    """Govern Friend execution without duplicating Friend runtime policy."""

    def __init__(self, plane: ResourceControlPlane):
        self._plane = plane

    def execute(
        self,
        request: FriendControlRequest,
        friend_executor: Callable[[dict[str, Any]], Any],
        *,
        measure: Callable[[Any, dict[str, Any]], MeasuredExecution],
    ) -> ExecutionResult:
        """Execute Friend work through the canonical control plane."""
        def governed_executor(route: dict[str, Any]) -> MeasuredExecution:
            value = friend_executor(route)
            measured = measure(value, route)
            if not isinstance(measured, MeasuredExecution):
                raise TypeError("Friend measurement must return MeasuredExecution")
            return measured

        return self._plane.execute(
            request_id=request.request_id,
            principal_id=request.principal_id,
            objective=request.objective,
            usage=request.usage,
            estimated_cost=request.estimated_cost,
            currency=request.currency,
            scopes=request.scopes,
            available_providers=request.available_providers,
            requested_agent=request.requested_agent,
            idempotency_key=request.idempotency_key,
            executor=governed_executor,
        )
