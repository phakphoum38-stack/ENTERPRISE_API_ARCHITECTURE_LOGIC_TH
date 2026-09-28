"""Economic budget primitives for Research OS resource governance.

Budgets are deliberately separate from quotas: quotas constrain resource
quantities, while budgets constrain estimated or realized economic cost.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from threading import RLock

from resource_governance import QuotaError


class BudgetDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class BudgetLimit:
    currency: str
    amount: Decimal

    def __post_init__(self) -> None:
        currency = self.currency.strip().upper()
        if len(currency) != 3 or not currency.isalpha():
            raise QuotaError("currency must be a three-letter code")
        if self.amount < Decimal("0"):
            raise QuotaError("budget amount must be non-negative")
        object.__setattr__(self, "currency", currency)


@dataclass(frozen=True)
class BudgetDecisionRecord:
    decision: BudgetDecision
    principal_id: str
    currency: str
    requested: Decimal
    committed: Decimal
    reserved: Decimal
    remaining: Decimal
    reason: str
    evaluated_at: datetime
    reservation_id: str | None = None


@dataclass(frozen=True)
class BudgetReservation:
    reservation_id: str
    principal_id: str
    amount: Decimal
    currency: str
    created_at: datetime


class BudgetLedger:
    """Thread-safe in-memory budget ledger for the governance foundation."""

    def __init__(self) -> None:
        self._limits: dict[str, BudgetLimit] = {}
        self._committed: dict[str, Decimal] = {}
        self._reservations: dict[str, BudgetReservation] = {}
        self._lock = RLock()
        self._sequence = 0

    def register(self, principal_id: str, limit: BudgetLimit) -> None:
        principal_id = principal_id.strip()
        if not principal_id:
            raise QuotaError("principal_id is required")
        with self._lock:
            self._limits[principal_id] = limit
            self._committed.setdefault(principal_id, Decimal("0"))

    def evaluate(self, principal_id: str, amount: Decimal, *, currency: str, now: datetime | None = None) -> BudgetDecisionRecord:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        amount = self._validate_amount(amount)
        with self._lock:
            limit = self._limit(principal_id)
            self._validate_currency(limit, currency)
            reserved = sum(r.amount for r in self._reservations.values() if r.principal_id == principal_id)
            committed = self._committed.get(principal_id, Decimal("0"))
            remaining = limit.amount - committed - reserved
            if amount > remaining:
                return BudgetDecisionRecord(BudgetDecision.DENY, principal_id, limit.currency, amount, committed, reserved, max(Decimal("0"), remaining), "budget_exceeded", now)
            return BudgetDecisionRecord(BudgetDecision.ALLOW, principal_id, limit.currency, amount, committed, reserved, remaining - amount, "within_budget", now)

    def reserve(self, principal_id: str, amount: Decimal, *, currency: str, now: datetime | None = None) -> BudgetDecisionRecord:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with self._lock:
            decision = self.evaluate(principal_id, amount, currency=currency, now=now)
            if decision.decision is BudgetDecision.DENY:
                return decision
            self._sequence += 1
            reservation_id = f"bres_{self._sequence:08d}"
            amount = self._validate_amount(amount)
            self._reservations[reservation_id] = BudgetReservation(reservation_id, principal_id, amount, decision.currency, now)
            post = self.evaluate(principal_id, Decimal("0"), currency=currency, now=now)
            return BudgetDecisionRecord(
                post.decision,
                post.principal_id,
                post.currency,
                amount,
                post.committed,
                post.reserved,
                post.remaining,
                "reserved",
                post.evaluated_at,
                reservation_id,
            )

    def commit(self, reservation_id: str, *, actual: Decimal | None = None) -> None:
        with self._lock:
            reservation = self._reservations.pop(reservation_id, None)
            if reservation is None:
                raise QuotaError("unknown budget reservation")
            amount = reservation.amount if actual is None else self._validate_amount(actual)
            if reservation.currency != self._currency(reservation.principal_id):
                raise QuotaError("budget currency mismatch")
            committed = self._committed.get(reservation.principal_id, Decimal("0"))
            limit = self._limit(reservation.principal_id)
            if committed + amount > limit.amount:
                raise QuotaError("budget commit exceeds limit")
            self._committed[reservation.principal_id] = committed + amount

    def release(self, reservation_id: str) -> None:
        with self._lock:
            if self._reservations.pop(reservation_id, None) is None:
                raise QuotaError("unknown budget reservation")

    def snapshot(self, principal_id: str) -> dict[str, str]:
        with self._lock:
            limit = self._limit(principal_id)
            reserved = sum(r.amount for r in self._reservations.values() if r.principal_id == principal_id)
            committed = self._committed.get(principal_id, Decimal("0"))
            return {"principal_id": principal_id, "currency": limit.currency, "limit": str(limit.amount), "committed": str(committed), "reserved": str(reserved), "remaining": str(limit.amount - committed - reserved)}

    @staticmethod
    def _validate_amount(amount: Decimal) -> Decimal:
        if not isinstance(amount, Decimal):
            raise QuotaError("budget amount must be Decimal")
        if amount.is_nan() or amount.is_infinite() or amount < Decimal("0"):
            raise QuotaError("budget amount must be finite and non-negative")
        return amount

    def _limit(self, principal_id: str) -> BudgetLimit:
        try:
            return self._limits[principal_id]
        except KeyError as exc:
            raise QuotaError("unknown principal budget") from exc

    def _currency(self, principal_id: str) -> str:
        return self._limit(principal_id).currency

    @staticmethod
    def _validate_currency(limit: BudgetLimit, currency: str) -> None:
        if currency.strip().upper() != limit.currency:
            raise QuotaError("budget currency mismatch")
