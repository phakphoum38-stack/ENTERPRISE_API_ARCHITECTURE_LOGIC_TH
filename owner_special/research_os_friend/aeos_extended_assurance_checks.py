"""Executable fail-closed implementations for the extended AEOS check set.

These checks are observation-driven. They require explicit evidence, freshness,
and independent verification before PASS can be returned. Missing or unsafe
observations remain UNKNOWN/BLOCKED rather than becoming implicit PASS.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class CheckState(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    STALE = "STALE"
    CONFLICT = "CONFLICT"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class CheckObservation:
    state: CheckState
    evidence_refs: tuple[str, ...]
    independent: bool
    fresh: bool
    details: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.state, CheckState):
            raise ValueError("state must be CheckState")
        if not self.evidence_refs or any(not isinstance(x, str) or not x for x in self.evidence_refs):
            raise ValueError("explicit evidence references are required")
        if type(self.independent) is not bool or type(self.fresh) is not bool:
            raise ValueError("independent and fresh must be strict booleans")
        if not isinstance(self.details, Mapping):
            raise ValueError("details must be a mapping")


_FORBIDDEN = frozenset({CheckState.UNKNOWN, CheckState.STALE, CheckState.CONFLICT, CheckState.BLOCKED})


def _evaluate(observation: CheckObservation, predicate: str) -> CheckState:
    if observation.state in _FORBIDDEN:
        return observation.state
    if observation.state is CheckState.FAIL:
        return CheckState.FAIL
    if not observation.independent or not observation.fresh:
        return CheckState.BLOCKED
    value = observation.details.get(predicate)
    if type(value) is not bool:
        return CheckState.UNKNOWN
    return CheckState.PASS if value else CheckState.FAIL


def dependency_integrity(o: CheckObservation) -> CheckState: return _evaluate(o, "dependency_integrity")
def dependency_provenance(o: CheckObservation) -> CheckState: return _evaluate(o, "dependency_provenance")
def semantic_compatibility(o: CheckObservation) -> CheckState: return _evaluate(o, "semantic_compatibility")
def version_monotonicity(o: CheckObservation) -> CheckState: return _evaluate(o, "version_monotonicity")
def backward_compatibility(o: CheckObservation) -> CheckState: return _evaluate(o, "backward_compatibility")
def forward_compatibility(o: CheckObservation) -> CheckState: return _evaluate(o, "forward_compatibility")
def migration_safety(o: CheckObservation) -> CheckState: return _evaluate(o, "migration_safety")
def rollback_migration(o: CheckObservation) -> CheckState: return _evaluate(o, "rollback_migration")
def identity_continuity(o: CheckObservation) -> CheckState: return _evaluate(o, "identity_continuity")
def delegation_chain(o: CheckObservation) -> CheckState: return _evaluate(o, "delegation_chain")
def confused_deputy(o: CheckObservation) -> CheckState: return _evaluate(o, "confused_deputy")
def capability_boundary(o: CheckObservation) -> CheckState: return _evaluate(o, "capability_boundary")
def policy_monotonicity(o: CheckObservation) -> CheckState: return _evaluate(o, "policy_monotonicity")
def agent_loop_safety(o: CheckObservation) -> CheckState: return _evaluate(o, "agent_loop_safety")
def retry_new_evidence(o: CheckObservation) -> CheckState: return _evaluate(o, "retry_new_evidence")
def tool_trust_boundary(o: CheckObservation) -> CheckState: return _evaluate(o, "tool_trust_boundary")
def instruction_boundary(o: CheckObservation) -> CheckState: return _evaluate(o, "instruction_boundary")
def model_version_drift(o: CheckObservation) -> CheckState: return _evaluate(o, "model_version_drift")
def lease_expiry(o: CheckObservation) -> CheckState: return _evaluate(o, "lease_expiry")
def distributed_lock(o: CheckObservation) -> CheckState: return _evaluate(o, "distributed_lock")
def idempotency(o: CheckObservation) -> CheckState: return _evaluate(o, "idempotency")
def deterministic_ordering(o: CheckObservation) -> CheckState: return _evaluate(o, "deterministic_ordering")
def rollback_readiness(o: CheckObservation) -> CheckState: return _evaluate(o, "rollback_readiness")
def state_reconstruction(o: CheckObservation) -> CheckState: return _evaluate(o, "state_reconstruction")
def disaster_recovery(o: CheckObservation) -> CheckState: return _evaluate(o, "disaster_recovery")
def failure_fingerprint(o: CheckObservation) -> CheckState: return _evaluate(o, "failure_fingerprint")
def failure_lineage(o: CheckObservation) -> CheckState: return _evaluate(o, "failure_lineage")
def regression_memory(o: CheckObservation) -> CheckState: return _evaluate(o, "regression_memory")
def root_cause_reintroduction(o: CheckObservation) -> CheckState: return _evaluate(o, "root_cause_reintroduction")
def evidence_coverage(o: CheckObservation) -> CheckState: return _evaluate(o, "evidence_coverage")
def evidence_tamper(o: CheckObservation) -> CheckState: return _evaluate(o, "evidence_tamper")
def evidence_conflict(o: CheckObservation) -> CheckState: return _evaluate(o, "evidence_conflict")
def evidence_revocation(o: CheckObservation) -> CheckState: return _evaluate(o, "evidence_revocation")
def audit_chain_integrity(o: CheckObservation) -> CheckState: return _evaluate(o, "audit_chain_integrity")
def audit_completeness(o: CheckObservation) -> CheckState: return _evaluate(o, "audit_completeness")
def assurance_coverage(o: CheckObservation) -> CheckState: return _evaluate(o, "assurance_coverage")
def blind_spot_discovery(o: CheckObservation) -> CheckState: return _evaluate(o, "blind_spot_discovery")
def no_self_merge(o: CheckObservation) -> CheckState: return _evaluate(o, "no_self_merge")
def no_evidence_as_authority(o: CheckObservation) -> CheckState: return _evaluate(o, "no_evidence_as_authority")
def no_merge_as_repair(o: CheckObservation) -> CheckState: return _evaluate(o, "no_merge_as_repair")


CHECK_SYMBOLS = {name.upper(): name for name in (
    "dependency_integrity", "dependency_provenance", "semantic_compatibility",
    "version_monotonicity", "backward_compatibility", "forward_compatibility",
    "migration_safety", "rollback_migration", "identity_continuity", "delegation_chain",
    "confused_deputy", "capability_boundary", "policy_monotonicity", "agent_loop_safety",
    "retry_new_evidence", "tool_trust_boundary", "instruction_boundary", "model_version_drift",
    "lease_expiry", "distributed_lock", "idempotency", "deterministic_ordering",
    "rollback_readiness", "state_reconstruction", "disaster_recovery", "failure_fingerprint",
    "failure_lineage", "regression_memory", "root_cause_reintroduction", "evidence_coverage",
    "evidence_tamper", "evidence_conflict", "evidence_revocation", "audit_chain_integrity",
    "audit_completeness", "assurance_coverage", "blind_spot_discovery", "no_self_merge",
    "no_evidence_as_authority", "no_merge_as_repair",
)}


def evaluate_check(check_id: str, observation: CheckObservation) -> CheckState:
    """Dispatch only to the explicit source implementation for a known check."""
    symbol = CHECK_SYMBOLS.get(check_id)
    if symbol is None:
        return CheckState.UNKNOWN
    return globals()[symbol](observation)
