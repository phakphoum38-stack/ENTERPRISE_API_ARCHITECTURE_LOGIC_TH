"""Canonical Resource Control boundary for Friend execution.

This adapter governs the existing FriendOrchestrator exactly once. It does not
create a second Brain, Factory, Provider, or policy runtime. Admission happens
before the orchestrator executes; accounting commits only an explicit
MeasuredExecution. Estimated cost is never silently settled as actual cost.
"""
from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import importlib
import os
from pathlib import Path
import sys
from typing import Any, TYPE_CHECKING
from uuid import uuid4

if TYPE_CHECKING:
    from tools.research_os_api.execution_contract import MeasuredExecution

_SCOPE = "agent:run"
_CURRENCY = "USD"


def _prepare_resource_control_imports() -> None:
    """Expose legacy flat imports while preserving one module identity per primitive."""
    module_root = Path(__file__).resolve().parents[2] / "tools" / "research_os_api"
    value = str(module_root)
    if value not in sys.path:
        sys.path.insert(0, value)
    for name in ("execution_contract", "resource_governance", "budgets", "api_keys", "admission", "agent_platform", "controlled_router", "policy", "resource_control_plane"):
        qualified = f"tools.research_os_api.{name}"
        module = importlib.import_module(qualified)
        sys.modules.setdefault(name, module)


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


def _build_plane(owner_id: str):
    _prepare_resource_control_imports()
    from budgets import BudgetLimit
    from resource_control_plane import ResourceControlPlane
    from resource_governance import Entitlement, Limit, QuotaDimension, Window

    plane = ResourceControlPlane()
    plane.register_principal(
        owner_id,
        Entitlement(
            "owner-special",
            scopes=frozenset({_SCOPE}),
            limits=(Limit(QuotaDimension.REQUESTS, Window.HOUR, _int_env("RESEARCH_OS_RESOURCE_REQUESTS_PER_HOUR", 1000, 0)),),
            max_concurrency=_int_env("RESEARCH_OS_RESOURCE_MAX_CONCURRENCY", 8, 1),
        ),
        BudgetLimit(_CURRENCY, _decimal_env("RESEARCH_OS_RESOURCE_BUDGET_USD", "1000000")),
    )
    return plane


def _measure_friend(value: Any, route: dict[str, Any]):
    _prepare_resource_control_imports()
    from execution_contract import MeasuredExecution
    from resource_governance import Usage

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
        usage = Usage(**{field: int(usage_payload.get(field, 0)) for field in ("requests", "tokens", "compute_units", "concurrent_jobs", "workers", "storage_bytes", "bandwidth_bytes")})
        return MeasuredExecution(value, usage, Decimal(str(actual_cost)), currency)
    provider = str(getattr(response, "provider", "") or route.get("provider") or "").strip().lower()
    if provider in {"owner-mock", "mock"}:
        return MeasuredExecution(value, Usage(requests=1), Decimal("0"), _CURRENCY)
    raise ValueError("authoritative Friend provider usage/cost is required; estimated cost cannot be settled as actual cost")


def _governed_ask(runtime: Any, request: Any):
    _prepare_resource_control_imports()
    from resource_control_friend import FriendControlRequest, FriendResourceControlAdapter
    from resource_governance import Usage

    plane = getattr(runtime, "_resource_control_plane", None)
    if plane is None:
        plane = _build_plane(runtime.owner.owner_id)
        runtime._resource_control_plane = plane
        runtime._resource_control_adapter = FriendResourceControlAdapter(plane)
    control_request = FriendControlRequest(
        request_id=_new_request_id(request.owner_id, request.session_id, request.text),
        principal_id=request.owner_id,
        objective=request.text,
        usage=Usage(requests=1),
        estimated_cost=_decimal_env("RESEARCH_OS_RESOURCE_ESTIMATED_COST_USD", "0"),
        currency=_CURRENCY,
        scopes=frozenset({_SCOPE}),
        available_providers=tuple(runtime.orchestrator.providers.names()),
    )
    captured: dict[str, Any] = {}

    def execute(route: dict[str, Any]) -> dict[str, Any]:
        response = runtime.orchestrator.handle(request)
        captured["response"] = response
        return {"provider": response.provider, "model": "friend-unified-master", "text": response.text, "response": response}

    result = runtime._resource_control_adapter.execute(control_request, execute, measure=_measure_friend)
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
