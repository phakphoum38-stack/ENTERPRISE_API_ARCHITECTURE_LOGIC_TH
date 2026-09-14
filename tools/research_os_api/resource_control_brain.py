"""Brain-to-resource-control planning boundary.

Brain remains the authority for logical workload/scale selection. This adapter
only converts that workload into an admission request; it does not create a
second quota or scale authority and it never invents post-execution usage.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable

from execution_contract import MeasuredExecution
from resource_control_plane import ExecutionResult, ResourceControlPlane
from resource_governance import Usage


@dataclass(frozen=True)
class BrainControlRequest:
    request_id: str
    principal_id: str
    objective: str
    leaf_tasks: int
    parallelism: int
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
        if self.leaf_tasks < 1:
            raise ValueError("leaf_tasks must be positive")
        if self.parallelism < 1:
            raise ValueError("parallelism must be positive")
        if self.estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative")


class BrainResourceControlAdapter:
    """Admit Brain work through the single ResourceControlPlane."""

    def __init__(self, plane: ResourceControlPlane):
        self._plane = plane

    def execute(
        self,
        request: BrainControlRequest,
        brain_executor: Callable[[dict[str, Any]], Any],
        *,
        measure: Callable[[Any, dict[str, Any]], MeasuredExecution],
    ) -> ExecutionResult:
        # Logical workload is an admission estimate. Actual provider/runtime
        # accounting must be supplied explicitly by the measurement callback.
        usage = Usage(
            requests=1,
            compute_units=request.leaf_tasks,
            concurrent_jobs=min(request.parallelism, request.leaf_tasks),
        )

        def governed_executor(route: dict[str, Any]) -> MeasuredExecution:
            value = brain_executor(route)
            measured = measure(value, route)
            if not isinstance(measured, MeasuredExecution):
                raise TypeError("Brain measurement must return MeasuredExecution")
            return measured

        return self._plane.execute(
            request_id=request.request_id,
            principal_id=request.principal_id,
            objective=request.objective,
            usage=usage,
            estimated_cost=request.estimated_cost,
            currency=request.currency,
            scopes=request.scopes,
            available_providers=request.available_providers,
            requested_agent=request.requested_agent,
            idempotency_key=request.idempotency_key,
            executor=governed_executor,
        )
