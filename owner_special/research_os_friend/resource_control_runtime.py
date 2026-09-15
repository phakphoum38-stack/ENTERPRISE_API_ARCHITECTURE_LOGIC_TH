"""Canonical Resource Control boundary for Friend execution.

This adapter governs the existing FriendOrchestrator exactly once.  It does not
create a second Brain, Factory, Provider, or policy runtime.  Admission happens
before the orchestrator executes; accounting commits only an explicit
MeasuredExecution.  Estimated cost is never silently settled as actual cost.
"""
from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import os
from typing import Any
from uuid import uuid4

from tools.research_os_api.budgets import BudgetLimit
from tools.research_os_api.execution_contract import MeasuredExecution
from tools.research_os_api.resource_control_friend import FriendResourceControlAdapter
from tools.research_os_api.resource_control_plane import ResourceControlPlane
from tools.research_os_api.resource_governance import Entitlement, Limit, QuotaDimension, Usage, Window


_SCOPE = "agent:run"
_CURRENCY = "USD"


def _int_env(name: str, default: int, minimum: int = 0) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    value = int(raw)
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _decimal_env(name: str, default: str) -> Decimal:
    raw = os.getenv(name, default).strip()
    value = Decimal(raw)
    if value.is_nan() or value.is_infinite() or value < Decimal("0"):
        raise ValueError(f"{name} must be finite and non-negative")
    return value


def _new_request_id(owner_id: str, session_id: str, text: str) -> str:
    nonce = uuid4().hex
    digest = sha256(f"{owner_id}\x00{session_id}\x00{text}\x00{nonce}".encode("utf-8")).hexdigest()[:24]
    return f"friend-{digest}"


def _build_plane(owner_id: str) -> ResourceControlPlane:
    requests_per_hour = _int_env("RESEARCH_OS_RESOURCE_REQUESTS_PER_HOUR", 1000, 0)
    max_concurrency = _int_env("RESEARCH_OS_RESOURCE_MAX_CONCURRENCY", 8, 1)
    budget_amount = _decimal_env("RESEARCH_OS_RESOURCE_BUDGET_USD", "1000000")
    plane = ResourceControlPlane()
    plane.register_principal(
        owner_id,
        Entitlement(
            "owner-special",
            scopes=frozenset({_SCOPE}),
            limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, requests_per_hour),),
            max_concurrency=max_concurrency,
        ),
        BudgetLimit(_CURRENCY, budget_amount),
    )
    return plane


def _measure_friend(value: Any, route: dict[str, Any]) -> MeasuredExecution:
    response = value.get("response") if isinstance(value, dict) else None
    if response is None:
        raise TypeError("Friend measurement requires the original FriendResponse")

    metadata = getattr(response, "metadata", {})
    resource = metadata.get("resource_control") if isinstance(metadata, dict) else None
    if isinstance(resource, dict):
        usage_payload = resource.get("usage")
        actual_cost = resource.get("actual_cost")
        currency = str(resource.get("currency") or _CURRENCY).strip().upper()
        if not isinstance(usage_payload, dict) or actual_cost is None:
            raise ValueError("Friend resource-control measurement is incomplete")
        usage = Usage(
            requests=int(usage_payload.get("requests", 1)),
            tokens=int(usage_payload.get("tokens", 0)),
            compute_units=int(usage_payload.get("compute_units", 0)),
            concurrent_jobs=int(usage_payload.get("concurrent_jobs", 0)),
            workers=int(usage_payload.get("workers", 0)),
            storage_bytes=int(usage_payload.get("storage_bytes", 0)),
            bandwidth_bytes=int(usage_payload.get("bandwidth_bytes", 0)),
        )
        return MeasuredExecution(value, usage, Decimal(str(actual_cost)), currency)

    provider = str(getattr(response, "provider", "") or route.get("provider") or "").strip().lower()
    if provider in {"owner-mock", "mock"}:
        return MeasuredExecution(value, Usage(requests=1), Decimal("0"), _CURRENCY)

    raise ValueError(
        "authoritative Friend provider usage/cost is required; "
        "estimated cost cannot be settled as actual cost"
    )


def _governed_ask(runtime: Any, request: Any):
    plane = getattr(runtime, "_resource_control_plane", None)
    if plane is None:
        plane = _build_plane(runtime.owner.owner_id)
        runtime._resource_control_plane = plane
        runtime._resource_control_adapter = FriendResourceControlAdapter(plane)

    request_id = _new_request_id(request.owner_id, request.session_id, request.text)
    estimated_cost = _decimal_env("RESEARCH_OS_RESOURCE_ESTIMATED_COST_USD", "0")
    body = {
        "request_id": request_id,
        "objective": request.text,
        "usage": {"requests": 1},
        "estimated_cost": str(estimated_cost),
        "currency": _CURRENCY,
        "scopes": [_SCOPE],
        "available_providers": list(runtime.orchestrator.providers.names()),
        "idempotency_key": None,
    }
    principal = type("FriendPrincipal", (), {"principal_id": request.owner_id, "scopes": frozenset({_SCOPE})})()
    captured: dict[str, Any] = {}

    def execute(route: dict[str, Any]) -> dict[str, Any]:
        response = runtime.orchestrator.handle(request)
        captured["response"] = response
        return {"provider": response.provider, "model": "friend-unified-master", "text": response.text, "response": response}

    result = runtime._resource_control_adapter.execute(
        body,
        principal,
        friend_executor=execute,
        measure=_measure_friend,
    )
    if result.admission.decision.value != "allow":
        raise PermissionError(result.admission.reason)
    response = captured.get("response")
    if response is None:
        raise RuntimeError("governed Friend execution produced no response")
    return response


def install_friend_resource_control() -> None:
    """Patch FriendRuntime.ask once, before OwnerFriendService starts serving."""
    from .runtime import FriendRuntime

    if getattr(FriendRuntime, "_resource_control_installed", False):
        return
    FriendRuntime.ask = _governed_ask  # type: ignore[method-assign]
    FriendRuntime._resource_control_installed = True
