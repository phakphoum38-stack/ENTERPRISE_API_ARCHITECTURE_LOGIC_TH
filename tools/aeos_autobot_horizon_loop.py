#!/usr/bin/env python3
"""Bounded single-pass H00-H27 Autobot control loop.

The loop coordinates discovery, causal consolidation, bounded repair and full
re-scan. It deliberately delegates source mutation and independent verification
to injected callables so the controller cannot silently acquire merge,
constitutional, or evidence-forging authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Callable, Iterable, Mapping


HORIZON = tuple(f"H{i:02d}" for i in range(28))


class HorizonLoopError(ValueError):
    """Raised for invalid controller input or unsafe repair output."""


class LoopState(str, Enum):
    DISCOVER = "DISCOVER"
    ANALYZE = "ANALYZE"
    GAP_SET_READY = "GAP_SET_READY"
    ROOT_CAUSE_READY = "ROOT_CAUSE_READY"
    REPAIR_PLANNED = "REPAIR_PLANNED"
    REPAIRING = "REPAIRING"
    VERIFYING = "VERIFYING"
    FULL_RESCAN = "FULL_RESCAN"
    FINISHED = "FINISHED"
    HARD_STOP = "HARD_STOP"


@dataclass(frozen=True)
class Finding:
    horizon: str
    dimension: str
    status: str
    symptom: str
    fingerprint: str
    root_cause: str | None = None


@dataclass(frozen=True)
class RepairSet:
    root_causes: tuple[str, ...]
    intents: tuple[str, ...]
    changed_files: tuple[str, ...]
    regression_tests: tuple[str, ...]
    fingerprint: str


@dataclass(frozen=True)
class LoopLimits:
    max_iterations: int = 10
    max_reanchors: int = 2
    max_ci_retries: int = 2
    max_unchanged_failure_retries: int = 1

    def validate(self) -> None:
        if not 1 <= self.max_iterations <= 50:
            raise HorizonLoopError("invalid_max_iterations")
        if not 0 <= self.max_reanchors <= 10:
            raise HorizonLoopError("invalid_max_reanchors")
        if not 0 <= self.max_ci_retries <= 10:
            raise HorizonLoopError("invalid_max_ci_retries")
        if not 0 <= self.max_unchanged_failure_retries <= 5:
            raise HorizonLoopError("invalid_max_unchanged_failure_retries")


@dataclass(frozen=True)
class LoopResult:
    state: LoopState
    source_sha: str
    iteration: int
    findings: tuple[Finding, ...]
    repair_sets: tuple[RepairSet, ...]
    hard_stop: str | None = None


def _sha256(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_horizon(findings: Iterable[Finding]) -> tuple[Finding, ...]:
    items = tuple(findings)
    seen = {item.horizon for item in items}
    if not seen.issubset(set(HORIZON)):
        raise HorizonLoopError("unknown_horizon")
    return items


def _failure_fingerprint(findings: Iterable[Finding]) -> str:
    values = sorted(item.fingerprint for item in findings if item.status != "PASS")
    return _sha256(values)


def collapse_root_causes(findings: Iterable[Finding]) -> tuple[str, ...]:
    roots = {item.root_cause for item in findings if item.status != "PASS" and item.root_cause}
    if any(item.status != "PASS" and not item.root_cause for item in findings):
        raise HorizonLoopError("ROOT_CAUSE_UNKNOWN")
    return tuple(sorted(roots))


def build_repair_set(findings: Iterable[Finding], repair_intents: Mapping[str, str],
                     changed_files: Iterable[str], regression_tests: Iterable[str]) -> RepairSet:
    items = _validate_horizon(findings)
    roots = collapse_root_causes(items)
    missing = [root for root in roots if root not in repair_intents]
    if missing:
        raise HorizonLoopError("repair_intent_missing")
    files = tuple(sorted(set(changed_files)))
    tests = tuple(sorted(set(regression_tests)))
    if not roots or not files or not tests:
        raise HorizonLoopError("incomplete_repair_set")
    if any(not isinstance(path, str) or not path or path.startswith("/") for path in files):
        raise HorizonLoopError("invalid_changed_file")
    intents = tuple(repair_intents[root] for root in roots)
    fingerprint = _sha256({"roots": roots, "intents": intents, "files": files, "tests": tests})
    return RepairSet(roots, intents, files, tests, fingerprint)


def run_horizon_loop(
    *,
    source_sha: str,
    discover: Callable[[str], Iterable[Finding]],
    plan_repair: Callable[[tuple[Finding, ...]], RepairSet],
    apply_repair: Callable[[RepairSet, str], str],
    verify: Callable[[str], Iterable[Finding]],
    independent_verify: Callable[[str], bool],
    limits: LoopLimits | None = None,
) -> LoopResult:
    """Run H00-H27 as one causal repair batch until FINISHED or HARD_STOP.

    ``apply_repair`` must return the new exact source SHA. The controller never
    performs git/ref/merge operations itself. Independent verification is a
    separate callable and must succeed before FINISHED is returned.
    """
    policy = limits or LoopLimits()
    policy.validate()
    if len(source_sha) != 40 or any(c not in "0123456789abcdef" for c in source_sha):
        raise HorizonLoopError("IDENTITY_MISMATCH")

    history: list[RepairSet] = []
    previous_failure_fp: str | None = None
    unchanged_retries = 0
    current_sha = source_sha

    for iteration in range(1, policy.max_iterations + 1):
        try:
            findings = _validate_horizon(discover(current_sha))
        except HorizonLoopError as exc:
            return LoopResult(LoopState.HARD_STOP, current_sha, iteration, (), tuple(history), str(exc))

        missing_h = set(HORIZON) - {item.horizon for item in findings}
        if missing_h:
            return LoopResult(LoopState.HARD_STOP, current_sha, iteration, findings, tuple(history), "INCOMPLETE_HORIZON")

        failures = tuple(item for item in findings if item.status != "PASS")
        if not failures:
            try:
                verified = independent_verify(current_sha)
            except Exception:
                verified = False
            if not verified:
                return LoopResult(LoopState.HARD_STOP, current_sha, iteration, findings, tuple(history), "INDEPENDENT_VERIFICATION_FAILED")
            return LoopResult(LoopState.FINISHED, current_sha, iteration, findings, tuple(history))

        failure_fp = _failure_fingerprint(failures)
        if failure_fp == previous_failure_fp:
            unchanged_retries += 1
            if unchanged_retries > policy.max_unchanged_failure_retries:
                return LoopResult(LoopState.HARD_STOP, current_sha, iteration, findings, tuple(history), "REPAIR_NOT_EFFECTIVE")
        else:
            unchanged_retries = 0
            previous_failure_fp = failure_fp

        try:
            repair = plan_repair(findings)
            if not repair.root_causes or not repair.changed_files or not repair.regression_tests:
                raise HorizonLoopError("incomplete_repair_set")
            new_sha = apply_repair(repair, current_sha)
            if len(new_sha) != 40 or any(c not in "0123456789abcdef" for c in new_sha):
                raise HorizonLoopError("IDENTITY_MISMATCH")
            if new_sha == current_sha:
                raise HorizonLoopError("REPAIR_DID_NOT_CHANGE_IDENTITY")
            history.append(repair)
            current_sha = new_sha
        except HorizonLoopError as exc:
            return LoopResult(LoopState.HARD_STOP, current_sha, iteration, findings, tuple(history), str(exc))
        except Exception:
            return LoopResult(LoopState.HARD_STOP, current_sha, iteration, findings, tuple(history), "REPAIR_FAILED")

    return LoopResult(LoopState.HARD_STOP, current_sha, policy.max_iterations, (), tuple(history), "BUDGET_EXHAUSTED")


if __name__ == "__main__":
    print("AEOS_H00_H27_AUTO_FIX_LOOP=READY")
