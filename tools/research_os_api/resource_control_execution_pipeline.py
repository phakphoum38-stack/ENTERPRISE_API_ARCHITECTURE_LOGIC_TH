"""Unified Friend -> Brain -> Factory -> Provider execution pipeline.

This is the canonical integration seam for the resource-control architecture.
The stages remain execution/planning owners; the ResourceControlPlane remains
the single admission, routing, accounting, and evidence authority.

Important: Friend/Brain/Factory stage callbacks here are deliberately *not*
wrapped by their individual resource-control adapters. Those adapters are
valid standalone boundaries, but nesting them would reserve/commit the same
work more than once. The unified runtime path admits exactly once, then runs
Friend -> Brain -> Factory -> Provider inside that governed execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Mapping

from .execution_contract import ExecutionContext, MeasuredExecution
from .resource_control_plane import ExecutionResult, ResourceControlPlane
from .resource_governance import Usage


@dataclass(frozen=True)
class UnifiedExecutionRequest:
    request_id: str
    principal_id: str
    objective: str
    usage: Usage
    estimated_cost: Decimal
    currency: str
    scopes: frozenset[str] = frozenset()
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


@dataclass(frozen=True)
class UnifiedExecutionContext:
    request: UnifiedExecutionRequest
    friend: Any
    brain: Any
    factory: Any


FriendStage = Callable[[UnifiedExecutionRequest], Any]
BrainStage = Callable[[UnifiedExecutionRequest, Any], Any]
FactoryStage = Callable[[UnifiedExecutionRequest, Any], Any]
ProviderStage = Callable[[ExecutionContext, Any], Any]
MeasureStage = Callable[[Any, ExecutionContext], MeasuredExecution]


class UnifiedResourceExecutionPipeline:
    """Run the complete logical execution path through one control plane."""

    def __init__(self, plane: ResourceControlPlane) -> None:
        self._plane = plane

    def execute(
        self,
        request: UnifiedExecutionRequest,
        *,
        friend: FriendStage,
        brain: BrainStage,
        factory: FactoryStage,
        provider: ProviderStage,
        measure: MeasureStage,
    ) -> ExecutionResult:
        """Plan Friend -> Brain -> Factory, then execute Provider under one gate."""
        friend_result = friend(request)
        brain_result = brain(request, friend_result)
        factory_result = factory(request, brain_result)
        context_holder: dict[str, UnifiedExecutionContext] = {}

        def governed_executor(route: dict[str, Any]) -> MeasuredExecution:
            provider_name = str(route.get("provider") or "unknown")
            model_name = str(route.get("model") or "unknown")
            execution_context = ExecutionContext(
                request_id=request.request_id,
                principal_id=request.principal_id,
                provider=provider_name,
                model=model_name,
                route=dict(route),
            )
            context_holder["value"] = UnifiedExecutionContext(
                request=request,
                friend=friend_result,
                brain=brain_result,
                factory=factory_result,
            )
            raw = provider(execution_context, factory_result)
            measured = measure(raw, execution_context)
            if not isinstance(measured, MeasuredExecution):
                raise TypeError("provider measurement must return MeasuredExecution")
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
