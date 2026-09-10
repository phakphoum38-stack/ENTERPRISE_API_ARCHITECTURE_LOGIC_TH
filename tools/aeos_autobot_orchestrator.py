#!/usr/bin/env python3
"""Fail-closed wave orchestrator for AEOS Autobot."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterable

from tools.aeos_autobot_evidence_manifest import evidence_id
from tools.aeos_autobot_state_machine import Barrier, Evidence, ResultState, Snapshot


@dataclass(frozen=True)
class Job:
    snapshot: Snapshot
    runner: Callable[[Snapshot], Evidence]


@dataclass(frozen=True)
class WaveResult:
    wave_id: str
    evidence: tuple[Evidence, ...]
    decision: ResultState


def run_wave(wave_id: str, jobs: Iterable[Job], *, max_workers: int = 8) -> WaveResult:
    job_list = list(jobs)
    if not job_list:
        return WaveResult(wave_id, (), ResultState.HOLD)
    if max_workers < 1:
        raise ValueError("invalid_max_workers")
    if any(job.snapshot.wave_id != wave_id for job in job_list):
        raise ValueError("wave_job_mismatch")

    first = job_list[0].snapshot
    if any(
        job.snapshot.iteration_id != first.iteration_id
        or job.snapshot.source_sha != first.source_sha
        for job in job_list
    ):
        raise ValueError("snapshot_lock_mismatch")

    required = frozenset(job.snapshot.set_id for job in job_list)
    if len(required) != len(job_list):
        raise ValueError("duplicate_set_id")
    barrier = Barrier(wave_id, required)
    evidence: list[Evidence] = []

    with ThreadPoolExecutor(max_workers=min(max_workers, len(job_list))) as pool:
        futures = {pool.submit(job.runner, job.snapshot): job for job in job_list}
        for future in as_completed(futures):
            job = futures[future]
            try:
                item = future.result()
            except Exception as exc:
                item = Evidence(job.snapshot, ResultState.INFRA_FAILED, evidence_id(job.snapshot, ResultState.INFRA_FAILED))
            if item.snapshot != job.snapshot:
                item = Evidence(job.snapshot, ResultState.STALE, evidence_id(job.snapshot, ResultState.STALE))
            elif item.evidence_id != evidence_id(item.snapshot, item.result_state):
                item = Evidence(job.snapshot, ResultState.HOLD, evidence_id(job.snapshot, ResultState.HOLD))
            try:
                barrier.accept(item)
            except ValueError:
                evidence.append(Evidence(job.snapshot, ResultState.HOLD, evidence_id(job.snapshot, ResultState.HOLD)))
            else:
                evidence.append(item)

    accepted_ids = {item.snapshot.set_id for item in barrier.evidence}
    if accepted_ids != set(required):
        return WaveResult(wave_id, tuple(evidence), ResultState.HOLD)
    return WaveResult(wave_id, tuple(evidence), barrier.decision())
