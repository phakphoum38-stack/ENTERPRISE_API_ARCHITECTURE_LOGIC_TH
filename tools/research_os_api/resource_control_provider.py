from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Mapping

from execution_contract import ExecutionContext, MeasuredExecution
from resource_control_plane import ExecutionResult, ResourceControlPlane
from resource_governance import Usage


@dataclass(frozen=True)
class ProviderControlRequest:
    request_id: str
    principal_id: str
    objective: str
    provider: str
    model: str
    estimated_usage: Usage
    estimated_cost: Decimal
    currency: str

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id is required")
        if not self.principal_id.strip():
            raise ValueError("principal_id is required")
        if not self.objective.strip():
            raise ValueError("objective is required")
        if not self.provider.strip():
            raise ValueError("provider is required")
        if not self.model.strip():
            raise ValueError("model is required")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative")
        if not self.currency.strip():
            raise ValueError("currency is required")


class ProviderResourceControlAdapter:
    """Makes provider execution subordinate to the canonical ResourceControlPlane."""

    def __init__(self, control_plane: ResourceControlPlane) -> None:
        self.control_plane = control_plane

    def execute(
        self,
        request: ProviderControlRequest,
        *,
        provider_execute: Callable[[ExecutionContext], object],
        measure: Callable[[object, ExecutionContext], MeasuredExecution],
    ) -> ExecutionResult:
        def run(route: dict[str, object]) -> MeasuredExecution:
            context = ExecutionContext(
                request_id=request.request_id,
                principal_id=request.principal_id,
                provider=str(route.get("provider") or request.provider),
                model=str(route.get("model") or request.model),
                route=dict(route),
            )
            raw = provider_execute(context)
            measured = measure(raw, context)
            if not isinstance(measured, MeasuredExecution):
                raise TypeError("provider measurement must return MeasuredExecution")
            return measured

        return self.control_plane.execute(
            request_id=request.request_id,
            principal_id=request.principal_id,
            objective=request.objective,
            usage=request.estimated_usage,
            estimated_cost=request.estimated_cost,
            currency=request.currency,
            executor=run,
        )
