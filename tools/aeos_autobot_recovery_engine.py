#!/usr/bin/env python3
"""Fail-closed, bounded HOLD recovery primitives for AEOS Autobot.

This module plans and records recovery only. It never mutates source and never
has merge authority. Re-verification is supplied by an external verifier.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import re
from typing import Callable

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_RE = re.compile(r"^[0-9a-f]{64}$")


class RecoveryState(str, Enum):
    HOLD_CREATED = "HOLD_CREATED"
    HOLD_CLASSIFIED = "HOLD_CLASSIFIED"
    RECOVERY_PLANNED = "RECOVERY_PLANNED"
    RECOVERY_AUTHORIZED = "RECOVERY_AUTHORIZED"
    RECOVERY_EXECUTED = "RECOVERY_EXECUTED"
    RE_VERIFIED = "RE_VERIFIED"
    RELEASE_HOLD = "RELEASE_HOLD"
    PROTECTED_HOLD = "PROTECTED_HOLD"


class RecoveryResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    CONFLICT = "CONFLICT"
    EXHAUSTED = "EXHAUSTED"


FAIL_REASONS = frozenset({
    "ROOT_CAUSE_UNPROVEN", "EVIDENCE_STALE", "EVIDENCE_CONFLICTED",
    "PROVENANCE_MISMATCH", "NEW_REGRESSION", "CONTROL_MISSING",
    "ASSURANCE_SELF_MODIFICATION", "AUTOBOT_EXHAUSTED",
    "INDEPENDENT_REVIEW_REQUIRED",
})


@dataclass(frozen=True)
class HoldRecord:
    hold_id: str
    iteration_id: str
    source_sha: str
    reason: str
    blocker: str
    evidence_ids: tuple[str, ...]

    def validate(self) -> None:
        if not self.hold_id or not self.iteration_id or not self.blocker:
            raise ValueError("hold_identity_missing")
        if not SHA_RE.fullmatch(self.source_sha):
            raise ValueError("invalid_source_sha")
        if self.reason not in FAIL_REASONS:
            raise ValueError("unknown_hold_reason")
        if not self.evidence_ids or any(not EVIDENCE_RE.fullmatch(item) for item in self.evidence_ids):
            raise ValueError("missing_or_invalid_blocker_evidence")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("duplicate_blocker_evidence")


@dataclass(frozen=True)
class RecoveryAttempt:
    hold_id: str
    iteration_id: str
    source_sha: str
    action: str
    attempt: int
    max_attempts: int
    authorized_by: str
    state: RecoveryState
    result: RecoveryResult | None
    evidence_id: str

    def validate(self, hold: HoldRecord) -> None:
        if self.hold_id != hold.hold_id or self.iteration_id != hold.iteration_id or self.source_sha != hold.source_sha:
            raise ValueError("recovery_identity_mismatch")
        if not self.action:
            raise ValueError("recovery_action_missing")
        if self.attempt < 1 or self.max_attempts < 1 or self.attempt > self.max_attempts:
            raise ValueError("invalid_recovery_attempt")
        if not self.authorized_by:
            raise ValueError("unauthorized_recovery")
        if not EVIDENCE_RE.fullmatch(self.evidence_id):
            raise ValueError("invalid_recovery_evidence_id")


def recovery_evidence_id(hold: HoldRecord, action: str, attempt: int, result: RecoveryResult) -> str:
    payload = f"{hold.hold_id}|{hold.iteration_id}|{hold.source_sha}|{action}|{attempt}|{result.value}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def classify_hold(hold: HoldRecord) -> RecoveryState:
    hold.validate()
    return RecoveryState.HOLD_CLASSIFIED


def plan_recovery(hold: HoldRecord, action: str, *, attempt: int, max_attempts: int) -> RecoveryAttempt:
    hold.validate()
    if not action:
        raise ValueError("recovery_action_missing")
    if max_attempts < 1 or attempt < 1 or attempt > max_attempts:
        raise ValueError("invalid_recovery_attempt")
    return RecoveryAttempt(hold.hold_id, hold.iteration_id, hold.source_sha, action, attempt, max_attempts, "", RecoveryState.RECOVERY_PLANNED, None, "0" * 64)


def authorize_recovery(plan: RecoveryAttempt, hold: HoldRecord, authorized_by: str) -> RecoveryAttempt:
    plan.validate(hold) if plan.authorized_by else None
    if plan.hold_id != hold.hold_id or plan.iteration_id != hold.iteration_id or plan.source_sha != hold.source_sha:
        raise ValueError("recovery_identity_mismatch")
    if not authorized_by:
        raise ValueError("unauthorized_recovery")
    return RecoveryAttempt(plan.hold_id, plan.iteration_id, plan.source_sha, plan.action, plan.attempt, plan.max_attempts, authorized_by, RecoveryState.RECOVERY_AUTHORIZED, None, "0" * 64)


def execute_recovery(plan: RecoveryAttempt, hold: HoldRecord, executor: Callable[[str], RecoveryResult]) -> RecoveryAttempt:
    if plan.state != RecoveryState.RECOVERY_AUTHORIZED:
        raise ValueError("recovery_not_authorized")
    plan.validate(hold)
    result = executor(plan.action)
    if result not in RecoveryResult:
        raise ValueError("invalid_recovery_result")
    state = RecoveryState.RECOVERY_EXECUTED
    return RecoveryAttempt(plan.hold_id, plan.iteration_id, plan.source_sha, plan.action, plan.attempt, plan.max_attempts, plan.authorized_by, state, result, recovery_evidence_id(hold, plan.action, plan.attempt, result))


def reverify(attempt: RecoveryAttempt, hold: HoldRecord, verifier: Callable[[RecoveryAttempt], RecoveryResult]) -> RecoveryState:
    attempt.validate(hold)
    if attempt.state != RecoveryState.RECOVERY_EXECUTED or attempt.result is None:
        raise ValueError("recovery_not_executed")
    verification = verifier(attempt)
    if verification == RecoveryResult.PASS:
        return RecoveryState.RELEASE_HOLD
    if verification == RecoveryResult.CONFLICT:
        return RecoveryState.PROTECTED_HOLD
    if attempt.attempt >= attempt.max_attempts:
        return RecoveryState.PROTECTED_HOLD
    return RecoveryState.HOLD_CLASSIFIED


def run_bounded_recovery(hold: HoldRecord, action: str, *, max_attempts: int, authorized_by: str, executor: Callable[[str], RecoveryResult], verifier: Callable[[RecoveryAttempt], RecoveryResult]) -> RecoveryState:
    hold.validate()
    if max_attempts < 1:
        raise ValueError("invalid_max_attempts")
    if not authorized_by:
        return RecoveryState.PROTECTED_HOLD
    for attempt_number in range(1, max_attempts + 1):
        plan = plan_recovery(hold, action, attempt=attempt_number, max_attempts=max_attempts)
        authorized = authorize_recovery(plan, hold, authorized_by)
        executed = execute_recovery(authorized, hold, executor)
        state = reverify(executed, hold, verifier)
        if state == RecoveryState.RELEASE_HOLD:
            return state
        if state == RecoveryState.PROTECTED_HOLD:
            return state
    return RecoveryState.PROTECTED_HOLD


if __name__ == "__main__":
    print("AEOS_AUTOBOT_RECOVERY_ENGINE=READY")
