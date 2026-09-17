"""HTTP boundary for the canonical governed execution paths.

HTTP is transport only. Identity is authenticated by the canonical session/API-key
layer; ResourceControlPlane remains the single authority for admission, routing,
execution accounting, and evidence.

The adapter supports two execution shapes: a generic Friend -> Brain -> Factory
-> Provider pipeline, and the already-composed Friend runtime exactly once.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Mapping

from execution_contract import MeasuredExecution
from resource_control_execution_pipeline import BrainStage, FactoryStage, FriendStage, MeasureStage, ProviderStage, UnifiedExecutionRequest, UnifiedResourceExecutionPipeline
from resource_control_friend import FriendControlRequest, FriendResourceControlAdapter
from resource_control_plane import ExecutionResult, ResourceControlPlane
from resource_governance import Usage

_USAGE_FIELDS = ("requests", "tokens", "compute_units", "concurrent_jobs", "workers", "storage_bytes", "bandwidth_bytes")


@dataclass(frozen=True)
class HTTPPrincipal:
    principal_id: str
    scopes: frozenset[str]

    def __post_init__(self) -> None:
        principal_id = self.principal_id.strip()
        if not principal_id:
            raise ValueError("principal_id is required")
        object.__setattr__(self, "principal_id", principal_id)
        object.__setattr__(self, "scopes", frozenset(str(scope).strip() for scope in self.scopes if str(scope).strip()))


@dataclass(frozen=True)
class ResourceControlHTTPRequest:
    request_id: str
    principal_id: str
    objective: str
    usage: Usage
    estimated_cost: Decimal
    currency: str
    scopes: frozenset[str]
    requested_agent: str | None
    available_providers: tuple[str, ...]
    idempotency_key: str | None

    def to_pipeline_request(self) -> UnifiedExecutionRequest:
        return UnifiedExecutionRequest(self.request_id, self.principal_id, self.objective, self.usage, self.estimated_cost, self.currency, self.scopes, self.available_providers, self.requested_agent, self.idempotency_key)

    def to_friend_request(self) -> FriendControlRequest:
        return FriendControlRequest(self.request_id, self.principal_id, self.objective, self.usage, self.estimated_cost, self.currency, self.scopes, self.available_providers, self.requested_agent, self.idempotency_key)


class ResourceControlHTTPAdapter:
    def __init__(self, plane: ResourceControlPlane):
        self._pipeline = UnifiedResourceExecutionPipeline(plane)
        self._friend_adapter = FriendResourceControlAdapter(plane)
        self._plane = plane

    def authenticate_api_key(self, raw_api_key: str, *, required_scope: str | None = None) -> HTTPPrincipal:
        record = self._plane.authenticate(raw_api_key, required_scope=required_scope)
        return HTTPPrincipal(record.principal_id, record.scopes)

    def normalize(self, body: Mapping[str, Any], principal: HTTPPrincipal) -> ResourceControlHTTPRequest:
        request_id = str(body.get("request_id") or "").strip()
        objective = str(body.get("objective") or body.get("prompt") or "").strip()
        currency = str(body.get("currency") or "USD").strip().upper()
        if not request_id:
            raise ValueError("request_id is required")
        if not objective:
            raise ValueError("objective is required")
        if not currency:
            raise ValueError("currency is required")
        usage_payload = body.get("usage") or {"requests": 1}
        if not isinstance(usage_payload, Mapping):
            raise ValueError("usage must be an object")
        unknown = sorted(set(usage_payload) - set(_USAGE_FIELDS))
        if unknown:
            raise ValueError(f"unknown usage dimensions: {', '.join(unknown)}")
        usage = Usage(**{field: int(usage_payload.get(field, 0)) for field in _USAGE_FIELDS})
        try:
            estimated_cost = Decimal(str(body.get("estimated_cost", "0")))
        except (ArithmeticError, ValueError) as exc:
            raise ValueError("estimated_cost must be a valid decimal") from exc
        if estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative")
        requested_scopes = frozenset(str(scope).strip() for scope in (body.get("scopes") or principal.scopes) if str(scope).strip())
        if not requested_scopes.issubset(principal.scopes):
            raise ValueError("requested scopes exceed authenticated principal scopes")
        providers = body.get("available_providers") or ()
        if isinstance(providers, str):
            providers = (providers,)
        if not isinstance(providers, (tuple, list)):
            raise ValueError("available_providers must be a list")
        return ResourceControlHTTPRequest(request_id, principal.principal_id, objective, usage, estimated_cost, currency, requested_scopes, str(body.get("requested_agent") or "").strip() or None, tuple(str(provider).strip() for provider in providers if str(provider).strip()), str(body.get("idempotency_key") or "").strip() or None)

    def execute(self, body: Mapping[str, Any], principal: HTTPPrincipal, *, friend: FriendStage, brain: BrainStage, factory: FactoryStage, provider: ProviderStage, measure: MeasureStage) -> ExecutionResult:
        request = self.normalize(body, principal)
        return self._pipeline.execute(request.to_pipeline_request(), friend=friend, brain=brain, factory=factory, provider=provider, measure=measure)

    def execute_friend(self, body: Mapping[str, Any], principal: HTTPPrincipal, *, friend_executor: Callable[[dict[str, Any]], Any], measure: Callable[[Any, dict[str, Any]], MeasuredExecution]) -> ExecutionResult:
        request = self.normalize(body, principal)
        return self._friend_adapter.execute(request.to_friend_request(), friend_executor, measure=measure)

    @staticmethod
    def response(result: ExecutionResult) -> dict[str, Any]:
        return {"request_id": result.request_id, "provider": result.provider, "model": result.model, "text": result.text, "usage": result.usage.__dict__ if result.usage else None, "cost": str(result.cost) if result.cost is not None else None, "currency": result.currency, "route": result.route, "admission": {"status": result.admission.status.value, "reservation_id": result.admission.reservation_id}, "ledger_sequence": result.ledger_entry.sequence if result.ledger_entry else None, "evidence_id": (result.evidence or {}).get("evidence_id") if result.evidence else None}
