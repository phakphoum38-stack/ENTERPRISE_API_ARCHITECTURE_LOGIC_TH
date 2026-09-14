"""Mandatory execution bridge for HTTP/Friend/Brain/Factory surfaces.

The bridge makes ResourceControlPlane the single admission and accounting
boundary. Execution adapters may provide the actual work, but they cannot
commit usage or cost outside the control plane.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Callable, Iterable

from resource_control_plane import ExecutionResult, ResourceControlPlane
from resource_governance import Usage


@dataclass(frozen=True)
class ExecutionEnvelope:
    """Provider/runtime result with mandatory measured accounting data."""

    value: Any
    usage: Usage
    cost: Decimal
    currency: str


@dataclass(frozen=True)
class GovernedExecutionRequest:
    request_id: str
    objective: str
    usage: Usage
    estimated_cost: Decimal
    currency: str
    required_scope: str | None = None
    idempotency_key: str | None = None
    principal_type: str = "user"
    available_providers: tuple[str, ...] = ()
    requested_agent: str | None = None
    allow_fallback: bool = True


class ResourceControlExecutionBridge:
    """Authenticated, fail-closed execution boundary for all runtime surfaces."""

    def __init__(self, control_plane: ResourceControlPlane) -> None:
        self.control_plane = control_plane

    def execute(
        self,
        raw_api_key: str,
        request: GovernedExecutionRequest,
        executor: Callable[[dict[str, Any]], ExecutionEnvelope],
    ) -> ExecutionResult:
        """Authenticate, admit, execute, and account through one control plane.

        The executor must return measured ``Usage`` and ``Decimal`` cost. The
        bridge deliberately refuses to infer actual accounting from estimates.
        """
        identity = self.control_plane.authenticate(
            raw_api_key,
            required_scope=request.required_scope,
        )
        scopes = frozenset(identity.scopes)
        providers: Iterable[str] | None = request.available_providers or None

        def governed_executor(route: dict[str, Any]) -> Any:
            envelope = executor(route)
            if not isinstance(envelope, ExecutionEnvelope):
                raise TypeError("executor must return ExecutionEnvelope")
            if envelope.cost < 0:
                raise ValueError("actual cost cannot be negative")
            if not envelope.currency.strip():
                raise ValueError("actual currency is required")
            return envelope

        # ResourceControlPlane.execute expects its executor result to be the
        # externally visible value and receives accounting separately. Capture
        # the measured envelope here, then commit exactly those measurements.
        measured: list[ExecutionEnvelope] = []

        def capture(route: dict[str, Any]) -> Any:
            envelope = governed_executor(route)
            measured.append(envelope)
            return envelope.value

        result = self.control_plane.execute(
            request_id=request.request_id,
            principal_id=identity.principal_id,
            objective=request.objective,
            usage=request.usage,
            estimated_cost=request.estimated_cost,
            currency=request.currency,
            executor=capture,
            scopes=scopes,
            principal_type=request.principal_type,
            idempotency_key=request.idempotency_key,
            available_providers=providers,
            requested_agent=request.requested_agent,
            allow_fallback=request.allow_fallback,
            actual_usage=measured[0].usage if measured else None,
            actual_cost=measured[0].cost if measured else None,
        )
        if result.ledger_entry is not None:
            measured_currency = measured[0].currency.strip().upper()
            if measured_currency != request.currency.strip().upper():
                raise ValueError("actual currency must match the admission currency")
        return result
