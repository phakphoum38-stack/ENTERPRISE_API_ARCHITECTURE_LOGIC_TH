"""HTTP-facing adapter for the unified Resource Control Plane.

This module is deliberately transport-oriented. It validates and normalizes an
HTTP request, then delegates admission, routing, execution accounting, ledger,
and evidence to the existing ResourceControlPlane. It does not create a second
quota, policy, budget, routing, or identity implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Mapping

from execution_contract import MeasuredExecution
from resource_control_plane import ExecutionResult, ResourceControlPlane
from resource_governance import Usage


_USAGE_FIELDS = (
    "requests",
    "tokens",
    "compute_units",
    "concurrent_jobs",
    "workers",
    "storage_bytes",
    "bandwidth_bytes",
)


@dataclass(frozen=True)
class HTTPPrincipal:
    """Identity already authenticated by the canonical session/API-key layer."""

    principal_id: str
    scopes: frozenset[str]

    def __post_init__(self) -> None:
        if not self.principal_id.strip():
            raise ValueError("principal_id is required")
        object.__setattr__(self, "principal_id", self.principal_id.strip())
        object.__setattr__(self, "scopes", frozenset(str(scope).strip() for scope in self.scopes if str(scope).strip()))


@dataclass(frozen=True)
class ResourceControlHTTPRequest:
    """Canonicalized HTTP request before it enters the control plane."""

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


class ResourceControlHTTPAdapter:
    """Translate an authenticated HTTP request into one control-plane call."""

    def __init__(self, plane: ResourceControlPlane):
        self._plane = plane

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

        usage_payload = body.get("usage")
        if usage_payload is None:
            usage_payload = {"requests": 1}
        if not isinstance(usage_payload, Mapping):
            raise ValueError("usage must be an object")
        unknown = sorted(set(usage_payload) - set(_USAGE_FIELDS))
        if unknown:
            raise ValueError(f"unknown usage dimensions: {', '.join(unknown)}")
        try:
            usage = Usage(**{field: int(usage_payload.get(field, 0)) for field in _USAGE_FIELDS})
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid usage: {exc}") from exc

        try:
            estimated_cost = Decimal(str(body.get("estimated_cost", "0")))
        except (ArithmeticError, ValueError) as exc:
            raise ValueError("estimated_cost must be a valid decimal") from exc
        if estimated_cost < 0:
            raise ValueError("estimated_cost cannot be negative")

        requested_scopes = frozenset(
            str(scope).strip() for scope in (body.get("scopes") or principal.scopes) if str(scope).strip()
        )
        if not requested_scopes.issubset(principal.scopes):
            raise ValueError("requested scopes exceed authenticated principal scopes")

        providers = body.get("available_providers") or ()
        if isinstance(providers, str):
            providers = (providers,)
        if not isinstance(providers, (tuple, list)):
            raise ValueError("available_providers must be a list")
        available_providers = tuple(str(provider).strip() for provider in providers if str(provider).strip())

        requested_agent = str(body.get("requested_agent") or "").strip() or None
        idempotency_key = str(body.get("idempotency_key") or "").strip() or None

        return ResourceControlHTTPRequest(
            request_id=request_id,
            principal_id=principal.principal_id,
            objective=objective,
            usage=usage,
            estimated_cost=estimated_cost,
            currency=currency,
            scopes=requested_scopes,
            requested_agent=requested_agent,
            available_providers=available_providers,
            idempotency_key=idempotency_key,
        )

    def execute(
        self,
        body: Mapping[str, Any],
        principal: HTTPPrincipal,
        executor: Callable[[dict[str, Any]], MeasuredExecution],
    ) -> ExecutionResult:
        request = self.normalize(body, principal)
        return self._plane.execute(
            request_id=request.request_id,
            principal_id=request.principal_id,
            objective=request.objective,
            usage=request.usage,
            estimated_cost=request.estimated_cost,
            currency=request.currency,
            scopes=request.scopes,
            requested_agent=request.requested_agent,
            available_providers=request.available_providers,
            idempotency_key=request.idempotency_key,
            executor=executor,
        )
