"""Single Research OS resource-control execution boundary.

This facade composes the existing credential, entitlement, policy, quota,
budget, routing, accounting, and evidence primitives. It deliberately does
not replace those primitives or own provider credentials. The goal is one
runtime boundary that can be embedded by HTTP, Friend, Brain, Factory, or
other execution surfaces without creating a second quota/policy system.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from hashlib import sha256
import json
from enum import Enum
from threading import RLock
from typing import Any, Callable, Iterable

from api_keys import APIKeyManager, APIKeyRecord
from admission import AdmissionRecord, AdmissionRequest, ResourceAdmissionGate
from agent_platform import AgentRouter
from budgets import BudgetLedger, BudgetLimit
from controlled_router import GovernedAgentRouter, GovernedRoute
from execution_contract import MeasuredExecution
from policy import PolicyEngine, PolicyRule
from resource_governance import Entitlement, ResourceGovernance, Usage


@dataclass(frozen=True)
class UsageLedgerEntry:
    sequence: int
    request_id: str
    principal_id: str
    admission_id: str
    provider: str
    model: str
    usage: Usage
    cost: Decimal
    currency: str
    status: str
    recorded_at: datetime
    previous_hash: str
    entry_hash: str


@dataclass(frozen=True)
class ExecutionResult:
    request_id: str
    admission: AdmissionRecord
    route: dict[str, Any] | None
    provider: str | None = None
    model: str | None = None
    text: str | None = None
    usage: Usage | None = None
    cost: Decimal | None = None
    currency: str | None = None
    ledger_entry: UsageLedgerEntry | None = None
    evidence: dict[str, Any] | None = None


@dataclass(frozen=True)
class _Principal:
    principal_id: str
    entitlement: Entitlement
    budget: BudgetLimit


class ResourceControlPlane:
    """One composition root for governed Research OS resource execution."""

    def __init__(self, *, api_keys: APIKeyManager | None = None, governance: ResourceGovernance | None = None, policy: PolicyEngine | None = None, budget: BudgetLedger | None = None, router: AgentRouter | None = None) -> None:
        self.api_keys = api_keys or APIKeyManager()
        self.governance = governance or ResourceGovernance()
        self.policy = policy or PolicyEngine()
        self.budget = budget or BudgetLedger()
        self.admission = ResourceAdmissionGate(self.governance, self.policy, self.budget)
        self.router = GovernedAgentRouter(self.admission, router or AgentRouter())
        self._principals: dict[str, _Principal] = {}
        self._ledger: list[UsageLedgerEntry] = []
        self._evidence: list[dict[str, Any]] = []
        self._evidence_root = "0" * 64
        self._lock = RLock()

    def register_principal(self, principal_id: str, entitlement: Entitlement, budget: BudgetLimit) -> None:
        principal_id = principal_id.strip()
        if not principal_id:
            raise ValueError("principal_id is required")
        self.governance.register(principal_id, entitlement)
        self.budget.register(principal_id, budget)
        with self._lock:
            self._principals[principal_id] = _Principal(principal_id, entitlement, budget)

    def add_policy_rule(self, rule: PolicyRule) -> None:
        self.policy.add_rule(rule)

    def create_api_key(self, principal_id: str, scopes: set[str] | frozenset[str], *, expires_at: datetime | None = None) -> tuple[APIKeyRecord, str]:
        self._require_principal(principal_id)
        entitlement = self.governance.entitlement(principal_id)
        if not frozenset(scopes).issubset(entitlement.scopes):
            raise ValueError("API-key scopes exceed entitlement scopes")
        return self.api_keys.create(principal_id, scopes, expires_at=expires_at)

    def authenticate(self, raw_api_key: str, *, required_scope: str | None = None) -> APIKeyRecord:
        record = self.api_keys.verify(raw_api_key, required_scope=required_scope)
        if record is None:
            raise PermissionError("invalid API key")
        self._require_principal(record.principal_id)
        return record

    def admit(self, *, request_id: str, principal_id: str, usage: Usage, estimated_cost: Decimal, currency: str, scopes: frozenset[str] = frozenset(), principal_type: str = "user", idempotency_key: str | None = None) -> AdmissionRecord:
        self._require_principal(principal_id)
        return self.admission.admit(AdmissionRequest(request_id=request_id, principal_id=principal_id, usage=usage, estimated_cost=estimated_cost, currency=currency, scopes=scopes, principal_type=principal_type, idempotency_key=idempotency_key))

    def route(self, *, request_id: str, principal_id: str, objective: str, usage: Usage, estimated_cost: Decimal, currency: str, scopes: frozenset[str] = frozenset(), principal_type: str = "user", idempotency_key: str | None = None, available_providers: Iterable[str] | None = None, requested_agent: str | None = None, allow_fallback: bool = True) -> GovernedRoute:
        self._require_principal(principal_id)
        return self.router.route(request_id=request_id, principal_id=principal_id, objective=objective, usage=usage, estimated_cost=estimated_cost, currency=currency, scopes=scopes, principal_type=principal_type, idempotency_key=idempotency_key, available_providers=available_providers, requested_agent=requested_agent, allow_fallback=allow_fallback)

    def execute(self, *, request_id: str, principal_id: str, objective: str, usage: Usage, estimated_cost: Decimal, currency: str, executor: Callable[[dict[str, Any]], Any], scopes: frozenset[str] = frozenset(), principal_type: str = "user", idempotency_key: str | None = None, available_providers: Iterable[str] | None = None, requested_agent: str | None = None, allow_fallback: bool = True, actual_usage: Usage | None = None, actual_cost: Decimal | None = None) -> ExecutionResult:
        governed = self.route(request_id=request_id, principal_id=principal_id, objective=objective, usage=usage, estimated_cost=estimated_cost, currency=currency, scopes=scopes, principal_type=principal_type, idempotency_key=idempotency_key, available_providers=available_providers, requested_agent=requested_agent, allow_fallback=allow_fallback)
        if not governed.allowed or governed.admission.reservation_id is None:
            return ExecutionResult(request_id, governed.admission, None)
        reservation_id = governed.admission.reservation_id
        try:
            value = executor(governed.route or {})
            measured, execution_value = self._resolve_measurement(value, admission_currency=currency, estimated_usage=usage, estimated_cost=estimated_cost, actual_usage=actual_usage, actual_cost=actual_cost)
            provider, model, text = self._normalize_execution(execution_value, governed.route)
            committed = self.router.commit(reservation_id, actual_usage=measured.usage, actual_cost=measured.cost)
            entry = self._record_usage(request_id=request_id, principal_id=principal_id, admission_id=reservation_id, provider=provider, model=model, usage=measured.usage, cost=measured.cost, currency=measured.currency, status=committed.status.value)
            evidence = self._record_evidence(request_id=request_id, principal_id=principal_id, admission_id=reservation_id, provider=provider, model=model, usage=measured.usage, cost=measured.cost, currency=measured.currency, ledger_hash=entry.entry_hash)
            return ExecutionResult(request_id, governed.admission, governed.route, provider, model, text, measured.usage, measured.cost, measured.currency, entry, evidence)
        except Exception:
            self.router.release(reservation_id)
            raise

    @staticmethod
    def _resolve_measurement(value: Any, *, admission_currency: str, estimated_usage: Usage, estimated_cost: Decimal, actual_usage: Usage | None, actual_cost: Decimal | None) -> tuple[MeasuredExecution, Any]:
        if isinstance(value, MeasuredExecution):
            expected = admission_currency.strip().upper()
            if value.currency != expected:
                raise ValueError("measured execution currency does not match admission currency")
            if actual_usage is not None and actual_usage != value.usage:
                raise ValueError("explicit actual_usage conflicts with measured execution")
            if actual_cost is not None and actual_cost != value.cost:
                raise ValueError("explicit actual_cost conflicts with measured execution")
            return value, value.value
        resolved_usage = actual_usage or estimated_usage
        resolved_cost = estimated_cost if actual_cost is None else actual_cost
        return MeasuredExecution(value, resolved_usage, resolved_cost, admission_currency), value

    def release(self, reservation_id: str):
        return self.router.release(reservation_id)

    def ledger(self) -> tuple[UsageLedgerEntry, ...]:
        with self._lock:
            return tuple(self._ledger)

    def evidence(self) -> tuple[dict[str, Any], ...]:
        with self._lock:
            return tuple(self._evidence)

    def forensic_snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {"principals": sorted(self._principals), "ledger_entries": len(self._ledger), "evidence_entries": len(self._evidence), "evidence_root": self._evidence_root, "ledger_hashes": [entry.entry_hash for entry in self._ledger]}

    def _record_usage(self, *, request_id: str, principal_id: str, admission_id: str, provider: str, model: str, usage: Usage, cost: Decimal, currency: str, status: str) -> UsageLedgerEntry:
        with self._lock:
            sequence = len(self._ledger) + 1
            recorded_at = datetime.now(timezone.utc)
            payload = {"sequence": sequence, "request_id": request_id, "principal_id": principal_id, "admission_id": admission_id, "provider": provider, "model": model, "usage": usage.__dict__, "cost": str(cost), "currency": currency.strip().upper(), "status": status, "recorded_at": recorded_at.isoformat(), "previous_hash": self._ledger[-1].entry_hash if self._ledger else "0" * 64}
            entry_hash = sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            entry = UsageLedgerEntry(sequence, request_id, principal_id, admission_id, provider, model, usage, cost, currency.strip().upper(), status, recorded_at, payload["previous_hash"], entry_hash)
            self._ledger.append(entry)
            return entry

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, Enum):
            return value.value
        if is_dataclass(value):
            return asdict(value)
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")

    def _record_evidence(self, **payload: Any) -> dict[str, Any]:
        with self._lock:
            record = dict(payload)
            record["sequence"] = len(self._evidence) + 1
            record["previous_hash"] = self._evidence_root
            record["recorded_at"] = datetime.now(timezone.utc).isoformat()
            canonical = json.dumps(record, sort_keys=True, separators=(",", ":"), default=self._json_default).encode()
            record["evidence_hash"] = sha256(canonical).hexdigest()
            self._evidence_root = record["evidence_hash"]
            self._evidence.append(record)
            return dict(record)

    @staticmethod
    def _normalize_execution(value: Any, route: dict[str, Any] | None) -> tuple[str, str, str | None]:
        route = route or {}
        provider = str(route.get("provider") or "unknown")
        model = str(route.get("model") or "unknown")
        if isinstance(value, dict):
            provider = str(value.get("provider") or provider)
            model = str(value.get("model") or model)
            return provider, model, value.get("text")
        return provider, model, str(value) if value is not None else None

    def _require_principal(self, principal_id: str) -> None:
        with self._lock:
            if principal_id not in self._principals:
                raise PermissionError("principal is not registered in the resource control plane")
