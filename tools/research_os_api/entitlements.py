"""Identity-to-entitlement binding primitives for Research OS.

This module bridges authenticated principals and the provider-agnostic resource
policy layer without becoming an authentication or persistence subsystem.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import RLock

from .resource_governance import Entitlement, QuotaError, ResourceGovernance


class EntitlementState(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


@dataclass(frozen=True)
class PrincipalBinding:
    principal_id: str
    entitlement: Entitlement
    state: EntitlementState = EntitlementState.ACTIVE
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.principal_id.strip():
            raise QuotaError("principal_id is required")
        if self.expires_at is not None and self.expires_at.tzinfo is None:
            raise QuotaError("expires_at must be timezone-aware")

    def active(self, now: datetime | None = None) -> bool:
        now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        return (
            self.state is EntitlementState.ACTIVE
            and (self.expires_at is None or self.expires_at > now)
        )


class EntitlementRegistry:
    """Thread-safe binding registry; persistence remains an external adapter."""

    def __init__(self, governance: ResourceGovernance | None = None) -> None:
        self._governance = governance or ResourceGovernance()
        self._bindings: dict[str, PrincipalBinding] = {}
        self._lock = RLock()

    @property
    def governance(self) -> ResourceGovernance:
        return self._governance

    def bind(self, binding: PrincipalBinding, *, now: datetime | None = None) -> None:
        if not binding.active(now):
            raise QuotaError("cannot bind inactive entitlement")
        with self._lock:
            self._bindings[binding.principal_id] = binding
            self._governance.register(binding.principal_id, binding.entitlement)

    def get(self, principal_id: str, *, now: datetime | None = None) -> PrincipalBinding:
        with self._lock:
            try:
                binding = self._bindings[principal_id]
            except KeyError as exc:
                raise QuotaError("unknown principal") from exc
            if not binding.active(now):
                raise QuotaError("principal entitlement is inactive")
            return binding

    def authorize_scope(
        self,
        principal_id: str,
        required_scope: str,
        *,
        now: datetime | None = None,
    ) -> PrincipalBinding:
        required_scope = required_scope.strip()
        if not required_scope:
            raise QuotaError("required_scope is required")
        binding = self.get(principal_id, now=now)
        if required_scope not in binding.entitlement.scopes:
            raise QuotaError("scope_not_entitled")
        return binding

    def suspend(self, principal_id: str) -> PrincipalBinding:
        return self._transition(principal_id, EntitlementState.SUSPENDED)

    def revoke(self, principal_id: str) -> PrincipalBinding:
        return self._transition(principal_id, EntitlementState.REVOKED)

    def restore(self, principal_id: str, *, now: datetime | None = None) -> PrincipalBinding:
        with self._lock:
            binding = self._binding(principal_id)
            restored = PrincipalBinding(
                principal_id=binding.principal_id,
                entitlement=binding.entitlement,
                state=EntitlementState.ACTIVE,
                expires_at=binding.expires_at,
            )
            if not restored.active(now):
                raise QuotaError("cannot restore expired entitlement")
            self._bindings[principal_id] = restored
            self._governance.register(principal_id, restored.entitlement)
            return restored

    def snapshot(self, principal_id: str, *, now: datetime | None = None) -> dict[str, object]:
        binding = self.get(principal_id, now=now)
        result = dict(self._governance.snapshot(principal_id, now=now))
        result.update({
            "principal_id": binding.principal_id,
            "entitlement_state": binding.state.value,
            "scopes": sorted(binding.entitlement.scopes),
            "expires_at": binding.expires_at.isoformat() if binding.expires_at else None,
            "priority": binding.entitlement.priority,
        })
        return result

    def _transition(self, principal_id: str, state: EntitlementState) -> PrincipalBinding:
        with self._lock:
            binding = self._binding(principal_id)
            updated = PrincipalBinding(
                principal_id=binding.principal_id,
                entitlement=binding.entitlement,
                state=state,
                expires_at=binding.expires_at,
            )
            self._bindings[principal_id] = updated
            return updated

    def _binding(self, principal_id: str) -> PrincipalBinding:
        try:
            return self._bindings[principal_id]
        except KeyError as exc:
            raise QuotaError("unknown principal") from exc
