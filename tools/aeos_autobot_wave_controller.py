#!/usr/bin/env python3
"""Fail-closed multi-wave controller for AEOS Autobot assurance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from tools.aeos_autobot_evidence_manifest import SnapshotLock, build_manifest, verify_manifest, write_manifest
from tools.aeos_autobot_orchestrator import Job, WaveResult, run_wave
from tools.aeos_autobot_state_machine import ResultState

WAVES: tuple[str, ...] = tuple(f"W{i}" for i in range(8))


@dataclass(frozen=True)
class ControllerLimits:
    max_iterations: int = 10
    max_runtime_seconds: float = 3600.0
    max_scope: int = 100
    max_changed_files: int = 100
    max_risk_level: int = 5

    def validate(self) -> None:
        if self.max_iterations < 1 or self.max_runtime_seconds <= 0:
            raise ValueError("invalid_execution_bounds")
        if self.max_scope < 1 or self.max_changed_files < 0 or self.max_risk_level < 0:
            raise ValueError("invalid_scope_bounds")


@dataclass(frozen=True)
class WaveRecord:
    wave_id: str
    result: WaveResult
    manifest_path: str | None


@dataclass(frozen=True)
class ControllerResult:
    iteration_id: str
    source_sha: str
    state: ResultState
    waves: tuple[WaveRecord, ...]


def _validate_jobs(wave_id: str, jobs: Iterable[Job], iteration_id: str, source_sha: str) -> list[Job]:
    items = list(jobs)
    if not items:
        raise ValueError(f"missing_required_wave:{wave_id}")
    for job in items:
        snapshot = job.snapshot
        if snapshot.wave_id != wave_id:
            raise ValueError("wave_job_mismatch")
        if snapshot.iteration_id != iteration_id or snapshot.source_sha != source_sha:
            raise ValueError("snapshot_lock_mismatch")
    return items


def run_controller(
    *,
    iteration_id: str,
    source_sha: str,
    waves: Mapping[str, Iterable[Job]],
    locks: Mapping[str, SnapshotLock] | None = None,
    manifest_dir: str | None = None,
    max_workers: int = 8,
    limits: ControllerLimits | None = None,
) -> ControllerResult:
    """Run W0..W7 with a hard barrier after every wave.

    A wave must have complete PASS evidence before the next wave starts. Any
    failure, timeout, stale result, identity mismatch, or manifest-integrity
    problem stops progression and returns HOLD. This controller never mutates
    source and has no merge authority.
    """
    if not iteration_id or len(source_sha) != 40 or any(c not in "0123456789abcdef" for c in source_sha):
        raise ValueError("invalid_controller_identity")
    if set(waves) - set(WAVES):
        raise ValueError("unknown_wave")
    policy = limits or ControllerLimits()
    policy.validate()
    if max_workers < 1:
        raise ValueError("invalid_max_workers")

    records: list[WaveRecord] = []
    for wave_id in WAVES:
        if wave_id not in waves:
            return ControllerResult(iteration_id, source_sha, ResultState.HOLD, tuple(records))
        try:
            jobs = _validate_jobs(wave_id, waves[wave_id], iteration_id, source_sha)
        except ValueError:
            return ControllerResult(iteration_id, source_sha, ResultState.HOLD, tuple(records))
        result = run_wave(wave_id, jobs, max_workers=max_workers)
        manifest_path: str | None = None

        if locks is not None:
            lock = locks.get(wave_id)
            if lock is None:
                records.append(WaveRecord(wave_id, result, None))
                return ControllerResult(iteration_id, source_sha, ResultState.HOLD, tuple(records))
            if lock.iteration_id != iteration_id or lock.source_sha != source_sha:
                records.append(WaveRecord(wave_id, result, None))
                return ControllerResult(iteration_id, source_sha, ResultState.HOLD, tuple(records))
            try:
                manifest = build_manifest(lock, wave_id, result.evidence, result.decision)
                if manifest_dir is not None:
                    from pathlib import Path
                    target = Path(manifest_dir) / f"aeos_autobot_{iteration_id}_{wave_id}.json"
                    write_manifest(manifest, target)
                    verify_manifest(target)
                    manifest_path = str(target)
            except (OSError, ValueError):
                records.append(WaveRecord(wave_id, result, None))
                return ControllerResult(iteration_id, source_sha, ResultState.HOLD, tuple(records))

        records.append(WaveRecord(wave_id, result, manifest_path))
        if result.decision != ResultState.PASSED:
            return ControllerResult(iteration_id, source_sha, ResultState.HOLD, tuple(records))

    return ControllerResult(iteration_id, source_sha, ResultState.PASSED, tuple(records))


if __name__ == "__main__":
    print("AEOS_AUTOBOT_WAVE_CONTROLLER=READY")
