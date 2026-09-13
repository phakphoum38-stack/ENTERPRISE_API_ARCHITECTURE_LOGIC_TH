"""Fail-closed bounded recovery for AEOS HOLD states.

This module is deliberately side-effect free with respect to repository/source
mutation. Recovery execution is delegated to an explicitly authorized caller.
Every attempt is bound to iteration_id + source_sha + hold_id and every release
requires an independent successful re-verification bound to the same identity
and authorization plan provenance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Mapping

MAX_ATTEMPTS = 3
MAX_EXECUTION_STEPS = 5


class RecoveryError(ValueError):
    """Raised when the recovery contract cannot safely proceed."""


class HoldDisposition(str, Enum):
    HOLD = "HOLD"
    PROTECTED_HOLD = "PROTECTED_HOLD"
    RELEASE_HOLD = "RELEASE_HOLD"


class HoldClass(str, Enum):
    STALE_SOURCE = "STALE_SOURCE"
    WRONG_ITERATION = "WRONG_ITERATION"
    MISSING_BLOCKER_EVIDENCE = "MISSING_BLOCKER_EVIDENCE"
    UNAUTHORIZED = "UNAUTHORIZED"
    FAILED_RECOVERY = "FAILED_RECOVERY"
    EXHAUSTED_ATTEMPTS = "EXHAUSTED_ATTEMPTS"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    RUNNING = "RUNNING"
    TIMEOUT = "TIMEOUT"
    INFRA_FAILED = "INFRA_FAILED"
    INCOMPLETE = "INCOMPLETE"
    UNKNOWN = "UNKNOWN"


# These classifications cannot authorize a recovery path or release a hold.
# Recoverable blocker states such as TIMEOUT may execute a bounded re-verification;
# their original state must never itself be treated as PASS.
PROTECTED_CLASSIFICATIONS = frozenset(
    {
        HoldClass.STALE_SOURCE,
        HoldClass.WRONG_ITERATION,
        HoldClass.MISSING_BLOCKER_EVIDENCE,
        HoldClass.CONFLICTING_EVIDENCE,
        HoldClass.UNAUTHORIZED,
        HoldClass.EXHAUSTED_ATTEMPTS,
        HoldClass.UNKNOWN,
    }
)

NEVER_PASS_STATES = frozenset(
    {"INCOMPLETE", "STALE", "MISMATCHED", "RUNNING", "TIMEOUT", "INFRA_FAILED", "CONFLICT", "UNKNOWN"}
)


@dataclass(frozen=True)
class Hold:
    hold_id: str
    iteration_id: str
    source_sha: str
    reason: str
    blocker_evidence: Mapping[str, Any] | None


@dataclass(frozen=True)
class RecoveryPlan:
    hold_id: str
    iteration_id: str
    source_sha: str
    classification: HoldClass
    attempt: int
    max_attempts: int = MAX_ATTEMPTS
    execution_steps: int = 1
    action: str = "reverify"


@dataclass(frozen=True)
class Authorization:
    hold_id: str
    iteration_id: str
    source_sha: str
    authorized: bool
    actor: str
    plan_fingerprint: str


@dataclass(frozen=True)
class RecoveryAttempt:
    hold_id: str
    iteration_id: str
    source_sha: str
    attempt: int
    classification: HoldClass
    status: str
    execution_steps: int
    evidence: Mapping[str, Any]
    plan_fingerprint: str


@dataclass(frozen=True)
class RecoveryRejection:
    hold_id: str
    iteration_id: str
    source_sha: str
    attempt: int
    classification: HoldClass
    reason: str
    plan_fingerprint: str
    actor: str


@dataclass
class RecoveryEngine:
    max_attempts: int = MAX_ATTEMPTS
    max_execution_steps: int = MAX_EXECUTION_STEPS
    attempts: list[RecoveryAttempt] = field(default_factory=list)
    rejections: list[RecoveryRejection] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 1 <= self.max_attempts <= MAX_ATTEMPTS:
            raise RecoveryError("max_attempts exceeds constitutional bound")
        if not 1 <= self.max_execution_steps <= MAX_EXECUTION_STEPS:
            raise RecoveryError("max_execution_steps exceeds constitutional bound")

    @staticmethod
    def _binding(hold_id: str, iteration_id: str, source_sha: str) -> tuple[str, str, str]:
        if not all(isinstance(x, str) and x for x in (hold_id, iteration_id, source_sha)):
            raise RecoveryError("hold_id, iteration_id, and source_sha are required")
        return hold_id, iteration_id, source_sha

    def classify(
        self,
        hold: Hold,
        *,
        expected_iteration_id: str,
        expected_source_sha: str,
        evidence: Mapping[str, Any] | None = None,
    ) -> HoldClass:
        self._binding(hold.hold_id, hold.iteration_id, hold.source_sha)
        if hold.source_sha != expected_source_sha:
            return HoldClass.STALE_SOURCE
        if hold.iteration_id != expected_iteration_id:
            return HoldClass.WRONG_ITERATION
        if evidence is None or not evidence:
            return HoldClass.MISSING_BLOCKER_EVIDENCE
        if evidence.get("conflict") is True:
            return HoldClass.CONFLICTING_EVIDENCE
        state = evidence.get("state")
        if state in {"running", "timeout", "infra_failed", "incomplete"}:
            return HoldClass(state.upper())
        if evidence.get("authorized") is False:
            return HoldClass.UNAUTHORIZED
        return HoldClass.UNKNOWN

    def reclassify(self, attempt: RecoveryAttempt) -> HoldClass:
        """Classify a non-PASS recovery result without ever upgrading it."""
        if attempt.status == "PASS":
            return attempt.classification
        if attempt.evidence.get("conflict") is True:
            return HoldClass.CONFLICTING_EVIDENCE
        return HoldClass.FAILED_RECOVERY

    def recovery_plan(self, hold: Hold, classification: HoldClass) -> RecoveryPlan:
        self._binding(hold.hold_id, hold.iteration_id, hold.source_sha)
        identity = (hold.hold_id, hold.iteration_id, hold.source_sha)
        prior = [
            a
            for a in self.attempts
            if (a.hold_id, a.iteration_id, a.source_sha) == identity
        ]
        attempt = len(prior) + 1
        if attempt > self.max_attempts:
            classification = HoldClass.EXHAUSTED_ATTEMPTS
        if classification in PROTECTED_CLASSIFICATIONS:
            action = "protected_hold"
        else:
            action = "reverify"
        return RecoveryPlan(
            hold.hold_id,
            hold.iteration_id,
            hold.source_sha,
            classification,
            attempt,
            self.max_attempts,
            1,
            action,
        )

    @staticmethod
    def authorize(plan: RecoveryPlan, authorization: Authorization) -> bool:
        if plan.classification in PROTECTED_CLASSIFICATIONS:
            return False
        return bool(
            authorization.authorized
            and authorization.actor
            and authorization.plan_fingerprint
            and authorization.hold_id == plan.hold_id
            and authorization.iteration_id == plan.iteration_id
            and authorization.source_sha == plan.source_sha
        )

    def _record_rejection(
        self,
        plan: RecoveryPlan,
        authorization: Authorization,
        reason: str,
    ) -> None:
        self.rejections.append(
            RecoveryRejection(
                plan.hold_id,
                plan.iteration_id,
                plan.source_sha,
                plan.attempt,
                plan.classification,
                reason,
                authorization.plan_fingerprint,
                authorization.actor,
            )
        )

    def execute(
        self,
        plan: RecoveryPlan,
        authorization: Authorization,
        executor: Callable[[RecoveryPlan], Mapping[str, Any]],
    ) -> RecoveryAttempt:
        if plan.classification in PROTECTED_CLASSIFICATIONS:
            self._record_rejection(plan, authorization, "protected_hold_classification")
            raise RecoveryError("recovery classification is PROTECTED_HOLD")
        if not self.authorize(plan, authorization):
            self._record_rejection(plan, authorization, "unauthorized recovery")
            raise RecoveryError("unauthorized recovery is PROTECTED_HOLD")
        if plan.attempt > self.max_attempts:
            self._record_rejection(plan, authorization, "recovery attempts exhausted")
            raise RecoveryError("recovery attempts exhausted")
        if plan.execution_steps > self.max_execution_steps:
            self._record_rejection(plan, authorization, "execution limit exceeded")
            raise RecoveryError("execution limit exceeded")
        result = executor(plan)
        if not isinstance(result, Mapping):
            self._record_rejection(plan, authorization, "recovery executor must return evidence mapping")
            raise RecoveryError("recovery executor must return evidence mapping")
        attempt = RecoveryAttempt(
            plan.hold_id,
            plan.iteration_id,
            plan.source_sha,
            plan.attempt,
            plan.classification,
            str(result.get("status", "FAIL")),
            plan.execution_steps,
            dict(result),
            authorization.plan_fingerprint,
        )
        self.attempts.append(attempt)
        return attempt

    def reverify(
        self,
        hold: Hold,
        attempt: RecoveryAttempt,
        verification: Mapping[str, Any],
    ) -> HoldDisposition:
        self._binding(hold.hold_id, hold.iteration_id, hold.source_sha)
        if (attempt.hold_id, attempt.iteration_id, attempt.source_sha) != (
            hold.hold_id,
            hold.iteration_id,
            hold.source_sha,
        ):
            return HoldDisposition.PROTECTED_HOLD
        if attempt.classification in PROTECTED_CLASSIFICATIONS:
            return HoldDisposition.PROTECTED_HOLD
        if verification.get("conflict") is True:
            return HoldDisposition.PROTECTED_HOLD
        if verification.get("source_sha") != hold.source_sha:
            return HoldDisposition.PROTECTED_HOLD
        if verification.get("iteration_id") != hold.iteration_id:
            return HoldDisposition.PROTECTED_HOLD
        if verification.get("hold_id") != hold.hold_id:
            return HoldDisposition.PROTECTED_HOLD
        if verification.get("plan_fingerprint") != attempt.plan_fingerprint:
            return HoldDisposition.PROTECTED_HOLD
        verification_state = verification.get("state")
        if verification_state in NEVER_PASS_STATES:
            return HoldDisposition.PROTECTED_HOLD
        if verification.get("status") == "PASS" and verification.get("authoritative") is True:
            return HoldDisposition.RELEASE_HOLD
        if attempt.attempt >= self.max_attempts:
            return HoldDisposition.PROTECTED_HOLD
        return HoldDisposition.HOLD

    def audit_record(self, hold: Hold, attempt: RecoveryAttempt) -> dict[str, Any]:
        return {
            "schema": "research-os-aeos-hold-recovery/v1",
            "hold_id": hold.hold_id,
            "iteration_id": hold.iteration_id,
            "source_sha": hold.source_sha,
            "attempt": attempt.attempt,
            "classification": self.reclassify(attempt).value,
            "status": attempt.status,
            "execution_steps": attempt.execution_steps,
            "plan_fingerprint": attempt.plan_fingerprint,
            "evidence": dict(attempt.evidence),
            "merge_authority": False,
            "self_certification": False,
        }

    @staticmethod
    def rejection_audit_record(rejection: RecoveryRejection) -> dict[str, Any]:
        return {
            "schema": "research-os-aeos-hold-recovery/v1",
            "hold_id": rejection.hold_id,
            "iteration_id": rejection.iteration_id,
            "source_sha": rejection.source_sha,
            "attempt": rejection.attempt,
            "classification": rejection.classification.value,
            "status": "REJECTED",
            "reason": rejection.reason,
            "plan_fingerprint": rejection.plan_fingerprint,
            "actor": rejection.actor,
            "merge_authority": False,
            "self_certification": False,
        }
