"""Executable governance, compatibility, audit, and integration integrity boundaries."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Mapping, Sequence


class IntegrityBoundaryError(ValueError):
    """Raised when an integrity invariant is violated."""


@dataclass(frozen=True)
class PolicySnapshot:
    version: int
    allowed_scopes: frozenset[str]
    deny_rules: frozenset[str]

    def is_monotonic_successor(self, previous: "PolicySnapshot") -> bool:
        """A successor may tighten policy, never widen authority or remove denies."""
        return (
            self.version == previous.version + 1
            and self.allowed_scopes.issubset(previous.allowed_scopes)
            and previous.deny_rules.issubset(self.deny_rules)
        )


def policy_monotonicity(previous: PolicySnapshot, current: PolicySnapshot) -> bool:
    if not isinstance(previous, PolicySnapshot) or not isinstance(current, PolicySnapshot):
        raise IntegrityBoundaryError("policy snapshots required")
    return current.is_monotonic_successor(previous)


@dataclass(frozen=True)
class ModelVersion:
    provider: str
    model: str
    version: str


def detect_model_version_drift(expected: ModelVersion, observed: ModelVersion) -> bool:
    """Return True only when the observed model identity differs from the bound one."""
    if not isinstance(expected, ModelVersion) or not isinstance(observed, ModelVersion):
        raise IntegrityBoundaryError("model versions required")
    return expected != observed


def model_version_drift(expected: ModelVersion, observed: ModelVersion) -> bool:
    return detect_model_version_drift(expected, observed)


@dataclass(frozen=True)
class SchemaProfile:
    version: int
    fields: Mapping[str, str]
    defaults: Mapping[str, object]


def semantic_compatibility(old: SchemaProfile, new: SchemaProfile) -> bool:
    """Require stable meanings for retained fields and explicit defaults for additions."""
    if new.version < old.version:
        return False
    for name, old_type in old.fields.items():
        if name in new.fields and new.fields[name] != old_type:
            return False
    return all(name in new.defaults for name in new.fields if name not in old.fields)


def backward_compatibility(old: SchemaProfile, new: SchemaProfile) -> bool:
    """An old consumer can read a new schema when retained field meanings are stable."""
    return semantic_compatibility(old, new)


def forward_compatibility(old: SchemaProfile, new: SchemaProfile) -> bool:
    """A new consumer can read an old schema when new fields have safe defaults."""
    if new.version < old.version:
        return False
    return all(name in old.fields or name in new.defaults for name in new.fields)


@dataclass(frozen=True)
class MigrationPlan:
    source_version: int
    target_version: int
    source_digest: str
    target_digest: str
    reversible: bool
    preconditions: tuple[str, ...]
    postconditions: tuple[str, ...]
    rollback_target: int | None


def migration_safety(plan: MigrationPlan) -> bool:
    """Migration is safe only with ordered versions, content bindings and explicit checks."""
    if not isinstance(plan, MigrationPlan):
        raise IntegrityBoundaryError("migration plan required")
    if plan.target_version <= plan.source_version:
        return False
    if len(plan.source_digest) != 64 or len(plan.target_digest) != 64:
        return False
    if not plan.preconditions or not plan.postconditions:
        return False
    if plan.reversible and plan.rollback_target != plan.source_version:
        return False
    return True


def rollback_migration(plan: MigrationPlan, observed_version: int, observed_digest: str) -> bool:
    """Rollback is valid only against the exact planned source recovery point."""
    return (
        migration_safety(plan)
        and plan.reversible
        and observed_version == plan.target_version
        and observed_digest == plan.target_digest
        and plan.rollback_target == plan.source_version
    )


@dataclass(frozen=True)
class AuditEntry:
    sequence: int
    event: str
    payload_digest: str
    previous_digest: str
    digest: str

    @staticmethod
    def compute_digest(sequence: int, event: str, payload_digest: str, previous_digest: str) -> str:
        payload = json.dumps(
            {"event": event, "payload_digest": payload_digest, "previous_digest": previous_digest, "sequence": sequence},
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()


def audit_chain_integrity(entries: Sequence[AuditEntry]) -> bool:
    """Verify contiguous ordering, hash linkage, and immutable entry digests."""
    previous = "0" * 64
    for expected_sequence, entry in enumerate(entries, start=1):
        if entry.sequence != expected_sequence or entry.previous_digest != previous:
            return False
        if entry.digest != AuditEntry.compute_digest(entry.sequence, entry.event, entry.payload_digest, entry.previous_digest):
            return False
        previous = entry.digest
    return True


def audit_completeness(entries: Sequence[AuditEntry], required_sequences: Sequence[int]) -> bool:
    """Require every declared audit sequence exactly once and a valid chain."""
    if not audit_chain_integrity(entries):
        return False
    actual = [entry.sequence for entry in entries]
    return actual == list(required_sequences)


def evidence_tamper(original_digest: str, observed_digest: str) -> bool:
    return original_digest == observed_digest and len(observed_digest) == 64


def evidence_conflict(digests: Sequence[str]) -> bool:
    return len(digests) > 0 and len(set(digests)) > 1


def evidence_revocation(revoked: bool) -> bool:
    return type(revoked) is bool and revoked


def no_self_merge(actor: str, source_owner: str) -> bool:
    """Self-evaluation actors may not be the merge authority."""
    if not isinstance(actor, str) or not isinstance(source_owner, str):
        raise IntegrityBoundaryError("merge identities required")
    return actor != source_owner


def no_merge_as_repair(merge_requested: bool, unresolved_failures: int, repair_in_progress: bool) -> bool:
    """A merge cannot be used to close or conceal unresolved repair work."""
    if type(merge_requested) is not bool or type(repair_in_progress) is not bool:
        raise IntegrityBoundaryError("strict booleans required")
    return not (merge_requested and (unresolved_failures > 0 or repair_in_progress))
