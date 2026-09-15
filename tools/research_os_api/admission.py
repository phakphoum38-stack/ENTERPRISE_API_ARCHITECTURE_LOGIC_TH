"""Unified Research OS resource admission and reservation gate.

This module composes the existing entitlement/quota, policy, and budget
primitives. It does not replace any of them: policy decides intent, quota
controls resource capacity, and budget controls economic capacity. A request
must pass all three before execution may proceed.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
import hashlib
import json
from threading import RLock

from budgets import BudgetDecision, BudgetLedger
from policy import PolicyContext, PolicyEffect, PolicyEngine
from resource_governance import Decision, Entitlement, QuotaError, ResourceGovernance, Usage


class AdmissionDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    THROTTLE = "throttle"


class AdmissionStatus(str, Enum):
    RESERVED = "reserved"
    COMMITTED = "committed"
    RELEASED = "released"
    EXPIRED = "expired"


@dataclass(frozen=True)
class AdmissionRequest:
    request_id: str
    principal_id: str
    usage: Usage
    estimated_cost: Decimal
    currency: str
    scopes: frozenset[str] = frozenset()
    principal_type: str = "user"
    idempotency_key: str | None = None

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise QuotaError("request_id is required")
        if not self.principal_id.strip():
            raise QuotaError("principal_id is required")
        if not isinstance(self.estimated_cost, Decimal):
            raise QuotaError("estimated_cost must be Decimal")
        if self.estimated_cost.is_nan() or self.estimated_cost.is_infinite() or self.estimated_cost < Decimal("0"):
            raise QuotaError("estimated_cost must be finite and non-negative")
        if len(self.currency.strip()) != 3 or not self.currency.strip().isalpha():
            raise QuotaError("currency must be a three-letter code")
        if self.idempotency_key is not None and not self.idempotency_key.strip():
            raise QuotaError("idempotency_key must not be empty")


@dataclass(frozen=True)
class AdmissionReservation:
    reservation_id: str
    request_id: str
    principal_id: str
    usage: Usage
    estimated_cost: Decimal
    currency: str
    quota_reservation_id: str
    budget_reservation_id: str
    created_at: datetime
    expires_at: datetime
    status: AdmissionStatus = AdmissionStatus.RESERVED
    fingerprint: str = ""


@dataclass(frozen=True)
class AdmissionRecord:
    decision: AdmissionDecision
    request_id: str
    principal_id: str
    reason: str
    reservation_id: str | None = None
    quota_reservation_id: str | None = None
    budget_reservation_id: str | None = None
    evaluated_at: datetime | None = None


class ResourceAdmissionGate:
    """Single deterministic gate joining policy, quota, and budget."""

    def __init__(
        self,
        governance: ResourceGovernance,
        policy: PolicyEngine,
        budget: BudgetLedger,
        *,
        reservation_ttl: timedelta = timedelta(minutes=5),
    ) -> None:
        if reservation_ttl <= timedelta(0):
            raise QuotaError("reservation_ttl must be positive")
        self._governance = governance
        self._policy = policy
        self._budget = budget
        self._reservation_ttl = reservation_ttl
        self._reservations: dict[str, AdmissionReservation] = {}
        self._idempotency: dict[str, tuple[str, str]] = {}
        self._sequence = 0
        self._lock = RLock()

    def admit(self, request: AdmissionRequest, *, now: datetime | None = None) -> AdmissionRecord:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        fingerprint = self._fingerprint(request)
        with self._lock:
            self._expire_locked(now)
            if request.idempotency_key:
                prior = self._idempotency.get(request.idempotency_key)
                if prior:
                    prior_fingerprint, prior_reservation_id = prior
                    if prior_fingerprint != fingerprint:
                        return self._deny(request, "idempotency_conflict", now)
                    reservation = self._reservations.get(prior_reservation_id)
                    if reservation is not None:
                        if reservation.status is AdmissionStatus.RESERVED:
                            return self._allow_from_reservation(reservation, now)
                        return self._allow_from_reservation(reservation, now)

            try:
                entitlement = self._governance.entitlement(request.principal_id)
            except QuotaError:
                return self._deny(request, "unknown_principal", now)

            if not request.scopes.issubset(entitlement.scopes):
                return self._deny(request, "scope_not_entitled", now)

            policy_decision = self._policy.evaluate(
                PolicyContext(request.principal_id, request.scopes, request.principal_type),
                request.usage,
            )
            if policy_decision.effect is PolicyEffect.DENY:
                return self._deny(request, f"policy_denied:{policy_decision.rule_id}", now)
            if policy_decision.effect is PolicyEffect.THROTTLE:
                return AdmissionRecord(AdmissionDecision.THROTTLE, request.request_id, request.principal_id, f"policy_throttled:{policy_decision.rule_id}", evaluated_at=now)

            quota = self._governance.reserve(request.principal_id, request.usage, now=now)
            if quota.decision is not Decision.ALLOW or quota.reservation_id is None:
                decision = AdmissionDecision.THROTTLE if quota.decision is Decision.THROTTLE else AdmissionDecision.DENY
                return AdmissionRecord(decision, request.request_id, request.principal_id, f"quota:{quota.reason}", evaluated_at=now)

            budget = self._budget.reserve(
                request.principal_id,
                request.estimated_cost,
                currency=request.currency,
                now=now,
            )
            if budget.decision is not BudgetDecision.ALLOW or budget.reservation_id is None:
                self._governance.release(quota.reservation_id)
                return self._deny(request, f"budget:{budget.reason}", now)

            self._sequence += 1
            reservation_id = f"ares_{self._sequence:08d}"
            reservation = AdmissionReservation(
                reservation_id,
                request.request_id,
                request.principal_id,
                request.usage,
                request.estimated_cost,
                request.currency.strip().upper(),
                quota.reservation_id,
                budget.reservation_id,
                now,
                now + self._reservation_ttl,
                fingerprint=fingerprint,
            )
            self._reservations[reservation_id] = reservation
            if request.idempotency_key:
                self._idempotency[request.idempotency_key] = (fingerprint, reservation_id)
            return AdmissionRecord(
                AdmissionDecision.ALLOW,
                request.request_id,
                request.principal_id,
                "reserved",
                reservation_id,
                quota.reservation_id,
                budget.reservation_id,
                now,
            )

    def commit(
        self,
        reservation_id: str,
        *,
        actual_usage: Usage | None = None,
        actual_cost: Decimal | None = None,
        now: datetime | None = None,
    ) -> AdmissionReservation:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with self._lock:
            reservation = self._reservations.get(reservation_id)
            if reservation is None:
                raise QuotaError("unknown admission reservation")
            if reservation.status is not AdmissionStatus.RESERVED:
                return reservation
            if reservation.expires_at <= now:
                self._release_locked(reservation, expired=True)
                raise QuotaError("admission reservation expired")
            usage = actual_usage or reservation.usage
            cost = reservation.estimated_cost if actual_cost is None else actual_cost
            self._validate_actual(reservation, usage, cost)
            self._governance.commit(reservation.quota_reservation_id, actual=usage, now=now)
            self._budget.commit(reservation.budget_reservation_id, actual=cost)
            updated = AdmissionReservation(**{**reservation.__dict__, "status": AdmissionStatus.COMMITTED})
            self._reservations[reservation_id] = updated
            return updated

    def release(self, reservation_id: str) -> AdmissionReservation:
        with self._lock:
            reservation = self._reservations.get(reservation_id)
            if reservation is None:
                raise QuotaError("unknown admission reservation")
            if reservation.status is AdmissionStatus.RESERVED:
                self._release_locked(reservation)
                reservation = self._reservations[reservation_id]
            return reservation

    def reservation(self, reservation_id: str) -> AdmissionReservation:
        with self._lock:
            try:
                return self._reservations[reservation_id]
            except KeyError as exc:
                raise QuotaError("unknown admission reservation") from exc

    def _release_locked(self, reservation: AdmissionReservation, *, expired: bool = False) -> None:
        self._governance.release(reservation.quota_reservation_id)
        self._budget.release(reservation.budget_reservation_id)
        status = AdmissionStatus.EXPIRED if expired else AdmissionStatus.RELEASED
        self._reservations[reservation.reservation_id] = AdmissionReservation(**{**reservation.__dict__, "status": status})

    def _expire_locked(self, now: datetime) -> None:
        for reservation in tuple(self._reservations.values()):
            if reservation.status is AdmissionStatus.RESERVED and reservation.expires_at <= now:
                self._release_locked(reservation, expired=True)

    @staticmethod
    def _validate_actual(reservation: AdmissionReservation, usage: Usage, cost: Decimal) -> None:
        for dimension in type(usage).__dataclass_fields__:
            if getattr(usage, dimension) > getattr(reservation.usage, dimension):
                raise QuotaError(f"actual usage exceeds reservation: {dimension}")
        if not isinstance(cost, Decimal) or cost.is_nan() or cost.is_infinite() or cost < Decimal("0"):
            raise QuotaError("actual_cost must be finite and non-negative Decimal")
        if cost > reservation.estimated_cost:
            raise QuotaError("actual cost exceeds reservation")

    @staticmethod
    def _fingerprint(request: AdmissionRequest) -> str:
        payload = {
            "request_id": request.request_id,
            "principal_id": request.principal_id,
            "usage": request.usage.__dict__,
            "estimated_cost": str(request.estimated_cost),
            "currency": request.currency.strip().upper(),
            "scopes": sorted(request.scopes),
            "principal_type": request.principal_type,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

    @staticmethod
    def _deny(request: AdmissionRequest, reason: str, now: datetime) -> AdmissionRecord:
        return AdmissionRecord(AdmissionDecision.DENY, request.request_id, request.principal_id, reason, evaluated_at=now)

    @staticmethod
    def _allow_from_reservation(reservation: AdmissionReservation, now: datetime) -> AdmissionRecord:
        return AdmissionRecord(
            AdmissionDecision.ALLOW,
            reservation.request_id,
            reservation.principal_id,
            reservation.status.value,
            reservation.reservation_id,
            reservation.quota_reservation_id,
            reservation.budget_reservation_id,
            now,
        )
