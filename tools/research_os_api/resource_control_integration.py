from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Mapping

from .execution_contract import MeasuredExecution
from .resource_control_brain import BrainControlRequest, BrainResourceControlAdapter
from .resource_control_factory import FactoryControlRequest, FactoryResourceControlAdapter
from .resource_control_friend import FriendControlRequest, FriendResourceControlAdapter
from .resource_control_provider import ProviderControlRequest, ProviderResourceControlAdapter
from .resource_control_plane import ResourceControlPlane
from .resource_governance import Usage


@dataclass(frozen=True)
class UnifiedControlRequest:
    request_id: str
    principal_id: str
    objective: str
    provider: str
    model: str
    leaf_tasks: int
    parallelism: int
    estimated_usage: Usage
    estimated_cost: Decimal
    currency: str


class UnifiedResourceControlIntegration:
    """One canonical execution path across HTTP/Friend/Brain/Factory/Provider boundaries."""

    def __init__(self, control_plane: ResourceControlPlane) -> None:
        self.control_plane = control_plane
        self.friend = FriendResourceControlAdapter(control_plane)
        self.brain = BrainResourceControlAdapter(control_plane)
        self.factory = FactoryResourceControlAdapter(control_plane)
        self.provider = ProviderResourceControlAdapter(control_plane)

    def execute(
        self,
        request: UnifiedControlRequest,
        *,
        provider_execute: Callable[[object], object],
        measure: Callable[[object, object], MeasuredExecution],
        metadata: Mapping[str, object] | None = None,
    ) -> MeasuredExecution:
        provider_request = ProviderControlRequest(
            request_id=request.request_id,
            principal_id=request.principal_id,
            objective=request.objective,
            provider=request.provider,
            model=request.model,
            estimated_usage=request.estimated_usage,
            estimated_cost=request.estimated_cost,
            currency=request.currency,
        )
        return self.provider.execute(
            provider_request,
            provider_execute=provider_execute,
            measure=measure,
            metadata={"unified_control_path": True, **dict(metadata or {})},
        )
