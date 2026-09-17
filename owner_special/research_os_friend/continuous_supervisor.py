"""P0-7 planning boundary for continuous supervisor decisions.

The supervisor does not execute work. It emits immutable decisions that an
existing queue/AEOS adapter may apply under its own lease and SHA invariants.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable
from .canonical_identity_federation import CanonicalIdentity, CanonicalIdentityError
from .canonical_attempt_identity import CanonicalAttempt

class SupervisorDecisionError(CanonicalIdentityError):
    """Raised when a supervisor decision would weaken lineage safety."""

@dataclass(frozen=True)
class SupervisorObservation:
    identity: CanonicalIdentity
    state: str
    dependencies_ready: bool
    lease_expired: bool = False
    verification_stale: bool = False
    conflict_detected: bool = False

@dataclass(frozen=True)
class SupervisorDecision:
    action: str
    identity: CanonicalIdentity
    reason: str
    requires_new_attempt: bool = False
    preserves_evidence: bool = True

ACTIONS = frozenset({"NOOP","SCHEDULE","RETRY","RECOVER","REBALANCE","RESCAN","QUARANTINE"})

def observe(*, identity: CanonicalIdentity, state: str, dependencies_ready: bool, lease_expired: bool=False, verification_stale: bool=False, conflict_detected: bool=False) -> SupervisorObservation:
    if not identity.mission_id or not identity.work_id or not identity.baseline_sha:
        raise SupervisorDecisionError("canonical identity is required")
    if conflict_detected:
        return SupervisorObservation(identity,state,dependencies_ready,lease_expired,verification_stale,True)
    return SupervisorObservation(identity,state,dependencies_ready,lease_expired,verification_stale,False)

def decide(observation: SupervisorObservation) -> SupervisorDecision:
    if observation.conflict_detected:
        return SupervisorDecision("QUARANTINE", observation.identity, "conflict detected; preserve evidence and stop mutation")
    if observation.lease_expired:
        return SupervisorDecision("RECOVER", observation.identity, "lease expired; recover through existing queue ownership rules")
    if observation.verification_stale:
        return SupervisorDecision("RESCAN", observation.identity, "verification evidence is stale; rescan before further trust")
    if observation.state in {"QUEUED","READY"} and observation.dependencies_ready:
        return SupervisorDecision("SCHEDULE", observation.identity, "dependencies satisfied")
    if observation.state in {"FAILED","RETRY_WAIT"}:
        return SupervisorDecision("RETRY", observation.identity, "retry through existing execution policy", requires_new_attempt=True)
    return SupervisorDecision("NOOP", observation.identity, "no supervisor action required")

def next_attempt(*, identity: CanonicalIdentity, attempt: CanonicalAttempt) -> CanonicalAttempt:
    if attempt.task_id != identity.task_id or attempt.run_id != identity.run_id:
        raise SupervisorDecisionError("attempt does not match canonical task/run")
    return attempt.retry(attempt_id=f"{attempt.attempt_id}:retry", attempt_number=attempt.attempt_number+1)
