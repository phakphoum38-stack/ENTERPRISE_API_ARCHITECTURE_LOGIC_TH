#!/usr/bin/env python3
"""Fail-closed AEOS Autobot state machine primitives.

This module intentionally does not execute commands or mutate source. It models
iteration identity, wave barriers, stale evidence rejection, and bounded recovery.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable


class State(str, Enum):
    OBSERVE = "OBSERVE"
    DIAGNOSE = "DIAGNOSE"
    PLAN_FIX = "PLAN_FIX"
    APPLY_FIX = "APPLY_FIX"
    RUN = "RUN"
    WAIT = "WAIT"
    COLLECT = "COLLECT"
    VERIFY = "VERIFY"
    NEXT_WAVE = "NEXT_WAVE"
    HOLD = "HOLD"
    READY_TO_MERGE = "READY_TO_MERGE"


class ResultState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    INFRA_FAILED = "INFRA_FAILED"
    CANCELLED = "CANCELLED"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Snapshot:
    iteration_id: str
    source_sha: str
    set_id: str
    wave_id: str
    command: str
    cwd: str

    def identity(self) -> str:
        return "|".join((self.iteration_id, self.source_sha, self.set_id, self.wave_id, self.command, self.cwd))


@dataclass(frozen=True)
class Evidence:
    snapshot: Snapshot
    result_state: ResultState
    evidence_id: str


@dataclass
class Barrier:
    wave_id: str
    required_set_ids: frozenset[str]
    evidence: list[Evidence] = field(default_factory=list)

    def accept(self, evidence: Evidence) -> None:
        if evidence.snapshot.wave_id != self.wave_id:
            raise ValueError("stale_evidence:wave_mismatch")
        if evidence.snapshot.set_id not in self.required_set_ids:
            raise ValueError("unexpected_set")
        if evidence.result_state in {ResultState.RUNNING, ResultState.QUEUED}:
            raise ValueError("incomplete_evidence")
        self.evidence.append(evidence)

    def complete(self) -> bool:
        ids = {item.snapshot.set_id for item in self.evidence}
        return ids == set(self.required_set_ids)

    def decision(self) -> ResultState:
        if not self.complete():
            return ResultState.HOLD
        if any(item.result_state != ResultState.PASSED for item in self.evidence):
            return ResultState.HOLD
        return ResultState.PASSED


def reject_stale(active: Snapshot, evidence: Evidence) -> None:
    if evidence.snapshot != active:
        raise ValueError("stale_or_cross_iteration_evidence")


def bounded_recovery_attempt(attempt: int, max_attempts: int) -> int:
    if max_attempts < 1:
        raise ValueError("invalid_max_attempts")
    if attempt < 0 or attempt >= max_attempts:
        raise RuntimeError("autobot_exhausted")
    return attempt + 1


def all_passed(results: Iterable[ResultState]) -> bool:
    values = list(results)
    return bool(values) and all(value == ResultState.PASSED for value in values)


if __name__ == "__main__":
    print("AEOS_AUTOBOT_STATE_MACHINE=READY")
