#!/usr/bin/env python3
"""Fail-closed wave orchestrator for AEOS Autobot.

The orchestrator coordinates already-declared jobs. It does not decide merge
authority, mutate source, or treat incomplete evidence as success.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable, Iterable

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
            except Exception as exc:  # fail closed: worker exceptions become failure evidence
                item = Evidence(job.snapshot, ResultState.INFRA_FAILED, f"worker_exception:{type(exc).__name__}")
            if item.snapshot != job.snapshot:
                item = Evidence(job.snapshot, ResultState.STALE, item.evidence_id)
            try:
                barrier.accept(item)
            except ValueError:
                evidence.append(Evidence(job.snapshot, ResultState.HOLD, item.evidence_id))
            else:
                evidence.append(item)

    # Barrier is the authoritative completion point. Every declared set must
    # have exactly one terminal result before the wave can advance.
    accepted_ids = {item.snapshot.set_id for item in barrier.evidence}
    if accepted_ids != set(required):
        return WaveResult(wave_id, tuple(evidence), ResultState.HOLD)
    return WaveResult(wave_id, tuple(evidence), barrier.decision())
