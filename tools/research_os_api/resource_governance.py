"""Research OS resource governance primitives.

This module is deliberately provider-agnostic and persistence-agnostic. It is the
canonical policy/decision layer for API-key entitlements and quota accounting;
HTTP handlers, databases, and provider adapters remain integration layers.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from threading import RLock
from typing import Mapping


class QuotaError(ValueError):
    pass


class QuotaDimension(str, Enum):
    REQUESTS = "requests"
    TOKENS = "tokens"
    COMPUTE_UNITS = "compute_units"
    CONCURRENT_JOBS = "concurrent_jobs"
    WORKERS = "workers"
    STORAGE_BYTES = "storage_bytes"
    BANDWIDTH_BYTES = "bandwidth_bytes"


class Window(str, Enum):
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    MONTH = "month"


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    THROTTLE = "throttle"


@dataclass(frozen=True)
class Limit:
    dimension: QuotaDimension
    window: Window
    amount: int

    def __post_init__(self) -> None:
        if not isinstance(self.dimension, QuotaDimension):
            raise QuotaError("invalid quota dimension")
        if not isinstance(self.window, Window):
            raise QuotaError("invalid quota window")
        if isinstance(self.amount, bool) or not isinstance(self.amount, int) or self.amount < 0:
            raise QuotaError("quota amount must be a non-negative integer")


@dataclass(frozen=True)
class Entitlement:
    tier: str
    scopes: frozenset[str] = frozenset()
    limits: tuple[Limit, ...] = ()
    priority: int = 0
    max_concurrency: int = 1

    def __post_init__(self) -> None:
        if not self.tier.strip():
            raise QuotaError("entitlement tier is required")
        if any(not isinstance(scope, str) or not scope.strip() for scope in self.scopes):
            raise QuotaError("entitlement scopes must be non-empty strings")
        seen: set[tuple[QuotaDimension, Window]] = set()
        for limit in self.limits:
            key = (limit.dimension, limit.window)
            if key in seen:
                raise QuotaError(f"duplicate quota limit: {limit.dimension.value}:{limit.window.value}")
            seen.add(key)
        if isinstance(self.priority, bool) or not isinstance(self.priority, int) or self.priority < 0:
            raise QuotaError("priority must be a non-negative integer")
        if isinstance(self.max_concurrency, bool) or not isinstance(self.max_concurrency, int) or self.max_concurrency < 1:
            raise QuotaError("max_concurrency must be a positive integer")


@dataclass(frozen=True)
class Usage:
    requests: int = 0
    tokens: int = 0
    compute_units: int = 0
    concurrent_jobs: int = 0
    workers: int = 0
    storage_bytes: int = 0
    bandwidth_bytes: int = 0

    def value(self, dimension: QuotaDimension) -> int:
        return {
            QuotaDimension.REQUESTS: self.requests,
            QuotaDimension.TOKENS: self.tokens,
            QuotaDimension.COMPUTE_UNITS: self.compute_units,
            QuotaDimension.CONCURRENT_JOBS: self.concurrent_jobs,
            QuotaDimension.WORKERS: self.workers,
            QuotaDimension.STORAGE_BYTES: self.storage_bytes,
            QuotaDimension.BANDWIDTH_BYTES: self.bandwidth_bytes,
        }[dimension]

    def __post_init__(self) -> None:
        values = (
            self.requests,
            self.tokens,
            self.compute_units,
            self.concurrent_jobs,
            self.workers,
            self.storage_bytes,
            self.bandwidth_bytes,
        )
        if any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in values):
            raise QuotaError("usage values must be non-negative integers")


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    principal_id: str
    usage: Usage
    created_at: datetime
    expires_at: datetime


@dataclass(frozen=True)
class DecisionRecord:
    decision: Decision
    principal_id: str
    reason: str
    reservation_id: str | None
    timestamp: datetime
    tier: str


@dataclass
class _PrincipalState:
    entitlement: Entitlement
    usage: dict[tuple[QuotaDimension, Window, datetime], int]
    reservations: dict[str, Reservation]

    def __init__(self, entitlement: Entitlement) -> None:
        self.entitlement = entitlement
        self.usage = {}
        self.reservations = {}


def _window_start(now: datetime, window: Window) -> datetime:
    now = now.astimezone(timezone.utc).replace(second=0, microsecond=0)
    if window is Window.MINUTE:
        return now
    if window is Window.HOUR:
        return now.replace(minute=0)
    if window is Window.DAY:
        return now.replace(hour=0)
    if window is Window.MONTH:
        return now.replace(day=1, hour=0, minute=0)
    raise QuotaError(f"unsupported quota window: {window}")


class ResourceGovernance:
    """Thread-safe quota decision engine with reservation semantics."""

    def __init__(self, *, reservation_ttl: timedelta = timedelta(minutes=5)) -> None:
        if reservation_ttl <= timedelta(0):
            raise QuotaError("reservation_ttl must be positive")
        self._reservation_ttl = reservation_ttl
        self._principals: dict[str, _PrincipalState] = {}
        self._lock = RLock()
        self._sequence = 0

    def register(self, principal_id: str, entitlement: Entitlement) -> None:
        principal_id = principal_id.strip()
        if not principal_id:
            raise QuotaError("principal_id is required")
        with self._lock:
            if principal_id in self._principals:
                raise QuotaError("principal already registered")
            self._principals[principal_id] = _PrincipalState(entitlement=entitlement)

    def update_entitlement(self, principal_id: str, entitlement: Entitlement) -> None:
        """Update a registered entitlement while preserving usage and reservations."""
        principal_id = principal_id.strip()
        if not principal_id:
            raise QuotaError("principal_id is required")
        with self._lock:
            state = self._state(principal_id)
            state.entitlement = entitlement

    def entitlement(self, principal_id: str) -> Entitlement:
        with self._lock:
            return self._state(principal_id).entitlement

    def evaluate(self, principal_id: str, usage: Usage, *, now: datetime | None = None) -> DecisionRecord:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with self._lock:
            state = self._state(principal_id)
            self._expire_reservations(state, now)
            for limit in state.entitlement.limits:
                requested = usage.value(limit.dimension)
                if requested == 0:
                    continue
                key = (limit.dimension, limit.window, _window_start(now, limit.window))
                used = state.usage.get(key, 0)
                reserved = sum(
                    r.usage.value(limit.dimension)
                    for r in state.reservations.values()
                    if r.expires_at > now
                )
                if used + reserved + requested > limit.amount:
                    return DecisionRecord(Decision.DENY, principal_id, f"quota_exceeded:{limit.dimension.value}:{limit.window.value}", None, now, state.entitlement.tier)
            concurrent = usage.concurrent_jobs
            if concurrent:
                active = sum(r.usage.concurrent_jobs for r in state.reservations.values() if r.expires_at > now)
                if active + concurrent > state.entitlement.max_concurrency:
                    return DecisionRecord(Decision.THROTTLE, principal_id, "concurrency_limit", None, now, state.entitlement.tier)
            return DecisionRecord(Decision.ALLOW, principal_id, "within_entitlement", None, now, state.entitlement.tier)

    def reserve(self, principal_id: str, usage: Usage, *, now: datetime | None = None) -> DecisionRecord:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with self._lock:
            decision = self.evaluate(principal_id, usage, now=now)
            if decision.decision is not Decision.ALLOW:
                return decision
            self._sequence += 1
            reservation_id = f"qres_{self._sequence:08d}"
            reservation = Reservation(reservation_id, principal_id, usage, now, now + self._reservation_ttl)
            self._state(principal_id).reservations[reservation_id] = reservation
            return DecisionRecord(Decision.ALLOW, principal_id, "reserved", reservation_id, now, decision.tier)

    def commit(self, reservation_id: str, *, actual: Usage | None = None, now: datetime | None = None) -> None:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with self._lock:
            principal_id, reservation = self._find_reservation(reservation_id)
            if reservation.expires_at <= now:
                raise QuotaError("reservation expired")
            usage = actual or reservation.usage
            self._validate_actual_within_reservation(reservation.usage, usage)
            state = self._state(principal_id)
            for limit in state.entitlement.limits:
                value = usage.value(limit.dimension)
                if value:
                    key = (limit.dimension, limit.window, _window_start(now, limit.window))
                    state.usage[key] = state.usage.get(key, 0) + value
            del state.reservations[reservation_id]

    def release(self, reservation_id: str) -> None:
        with self._lock:
            principal_id, _ = self._find_reservation(reservation_id)
            del self._state(principal_id).reservations[reservation_id]

    def snapshot(self, principal_id: str, *, now: datetime | None = None) -> Mapping[str, int | str]:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        with self._lock:
            state = self._state(principal_id)
            self._expire_reservations(state, now)
            result: dict[str, int | str] = {"tier": state.entitlement.tier}
            for limit in state.entitlement.limits:
                key = (limit.dimension, limit.window, _window_start(now, limit.window))
                result[f"{limit.dimension.value}:{limit.window.value}:limit"] = limit.amount
                result[f"{limit.dimension.value}:{limit.window.value}:used"] = state.usage.get(key, 0)
            return result

    @staticmethod
    def _validate_actual_within_reservation(reserved: Usage, actual: Usage) -> None:
        for dimension in QuotaDimension:
            if actual.value(dimension) > reserved.value(dimension):
                raise QuotaError(f"actual usage exceeds reservation: {dimension.value}")

    def _state(self, principal_id: str) -> _PrincipalState:
        try:
            return self._principals[principal_id]
        except KeyError as exc:
            raise QuotaError("unknown principal") from exc

    def _find_reservation(self, reservation_id: str) -> tuple[str, Reservation]:
        for principal_id, state in self._principals.items():
            reservation = state.reservations.get(reservation_id)
            if reservation is not None:
                return principal_id, reservation
        raise QuotaError("unknown reservation")

    @staticmethod
    def _expire_reservations(state: _PrincipalState, now: datetime) -> None:
        expired = [rid for rid, reservation in state.reservations.items() if reservation.expires_at <= now]
        for rid in expired:
            del state.reservations[rid]
