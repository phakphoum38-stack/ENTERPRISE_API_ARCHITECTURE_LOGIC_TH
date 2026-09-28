"""Factory-facing resource-control boundary.

The factory is an execution planner, not a second resource-governance system.
It converts a planned workload into one governed execution request and leaves
quota, budget, policy, routing, accounting, and evidence ownership to the
canonical ResourceControlPlane.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Iterable

from execution_contract import MeasuredExecution
from resource_control_plane import ExecutionResult, ResourceControlPlane
from resource_governance import Usage


@dataclass(frozen=True)
class FactoryWorkload:
    """Normalized logical workload produced by Brain/Factory planning."""

    request_id: str
    principal_id: str
    objective: str
    leaf_tasks: int
    parallelism: int = 1
    scopes: frozenset[str] = frozenset()
    estimated_cost: Decimal = Decimal("0")
    currency: str = "USD"
    idempotency_key: str | None = None
    available_providers: tuple[str, ...] = ()
    requested_agent: str | None = None

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
        object.__setattr__(self, "currency", self.currency.strip().upper())
        if not self.currency:
            raise ValueError("currency is required")


class ResourceControlledFactory:
    """Submit factory execution through the single resource-control plane."""

    def __init__(self, plane: ResourceControlPlane):
        self._plane = plane

    @staticmethod
    def reserve_usage(workload: FactoryWorkload) -> Usage:
        """Translate logical workload into conservative admission dimensions."""
        return Usage(
            requests=1,
            tokens=0,
            compute_units=max(1, workload.leaf_tasks),
            concurrent_jobs=max(1, workload.parallelism),
        )

    def execute(
        self,
        workload: FactoryWorkload,
        executor: Callable[[dict[str, Any]], MeasuredExecution],
    ) -> ExecutionResult:
        usage = self.reserve_usage(workload)
        return self._plane.execute(
            request_id=workload.request_id,
            principal_id=workload.principal_id,
            objective=workload.objective,
            usage=usage,
            estimated_cost=workload.estimated_cost,
            currency=workload.currency,
            scopes=workload.scopes,
            idempotency_key=workload.idempotency_key,
            available_providers=workload.available_providers,
            requested_agent=workload.requested_agent,
            executor=executor,
        )


def measured_factory_result(
    value: Any,
    *,
    usage: Usage,
    cost: Decimal,
    currency: str,
) -> MeasuredExecution:
    """Explicit helper for Factory adapters to report actual execution."""
    return MeasuredExecution(value, usage, cost, currency)
