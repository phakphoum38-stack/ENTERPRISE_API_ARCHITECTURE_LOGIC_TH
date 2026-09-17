"""Governed runtime routing boundary for Research OS agents.

The existing AgentRouter remains responsible for capability/provider selection.
This adapter makes ResourceAdmissionGate the mandatory pre-execution boundary:
no agent/provider route is returned as executable until entitlement, policy,
quota, and budget admission has succeeded.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Iterable

from admission import AdmissionDecision, AdmissionRecord, AdmissionRequest, ResourceAdmissionGate
from agent_platform import AgentRouter
from resource_governance import Usage


@dataclass(frozen=True)
class GovernedRoute:
    admission: AdmissionRecord
    route: dict[str, Any] | None

    @property
    def allowed(self) -> bool:
        return self.admission.decision is AdmissionDecision.ALLOW and self.route is not None


class GovernedAgentRouter:
    """Compose runtime routing with the single Resource Control Plane gate."""

    def __init__(self, admission: ResourceAdmissionGate, router: AgentRouter | None = None) -> None:
        self._admission = admission
        self._router = router or AgentRouter()

    def route(
        self,
        *,
        request_id: str,
        principal_id: str,
        objective: str,
        usage: Usage,
        estimated_cost: Decimal,
        currency: str,
        scopes: frozenset[str] = frozenset(),
        principal_type: str = "user",
        idempotency_key: str | None = None,
        available_providers: Iterable[str] | None = None,
        requested_agent: str | None = None,
        allow_fallback: bool = True,
    ) -> GovernedRoute:
        admission = self._admission.admit(
            AdmissionRequest(
                request_id=request_id,
                principal_id=principal_id,
                usage=usage,
                estimated_cost=estimated_cost,
                currency=currency,
                scopes=scopes,
                principal_type=principal_type,
                idempotency_key=idempotency_key,
            )
        )
        if admission.decision is not AdmissionDecision.ALLOW:
            return GovernedRoute(admission=admission, route=None)

        try:
            route = self._router.route(
                objective,
                requested_agent=requested_agent,
                available_providers=available_providers,
                allow_fallback=allow_fallback,
            )
            provider_selection = route.get("provider_selection") or {}
            route = {
                **route,
                "provider": provider_selection.get("provider"),
                "model": (provider_selection.get("model") or ""),
            }
        except Exception:
            self._admission.release(admission.reservation_id)  # type: ignore[arg-type]
            raise
        return GovernedRoute(admission=admission, route=route)

    def commit(
        self,
        reservation_id: str,
        *,
        actual_usage: Usage | None = None,
        actual_cost: Decimal | None = None,
    ):
        return self._admission.commit(
            reservation_id,
            actual_usage=actual_usage,
            actual_cost=actual_cost,
        )

    def release(self, reservation_id: str):
        return self._admission.release(reservation_id)
