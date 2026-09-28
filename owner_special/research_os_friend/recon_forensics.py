"""RECON adapter for the universal forensic execution-boundary layer.

This adapter is deliberately planning-only: normal RECON failure ingestion does
not execute probes, mutate source, or grant authority. It translates a failure
record into a bounded diagnostic plan that can be executed explicitly by a
forensic caller and then evaluated by ``tools.forensics.execution.isolate``.

The adapter uses a structural failure contract rather than importing the staged
RECON failure implementation. This keeps the forensic layer independently
usable while remaining compatible with ``ReconFailure`` once that module is
present.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Protocol

from tools.forensics.execution import bounded_worker_matrix

_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class FailureRecord(Protocol):
    source_sha: str
    failure_fingerprint: str
    kind: object


class ProbeFamily(str, Enum):
    DIRECT = "direct"
    SHELL = "shell"
    PLATFORM = "platform"


@dataclass(frozen=True)
class ReconForensicPlan:
    target_sha: str
    source_sha: str
    failure_fingerprint: str
    kind: str
    probes: tuple[ProbeFamily, ...]
    worker_matrix: tuple[int, ...]
    auto_execute: bool = False


def _kind_name(kind: object) -> str:
    value = getattr(kind, "value", kind)
    if not isinstance(value, str) or not value:
        raise ValueError("failure.kind must expose a non-empty string value")
    return value


def build_forensic_plan(
    failure: FailureRecord,
    *,
    target_sha: str,
    worker_values: tuple[int, ...] = (1, 4, 16),
    maximum_workers: int = 16,
) -> ReconForensicPlan:
    """Build a bounded plan from a RECON failure without executing anything."""
    if not _SHA1_RE.fullmatch(target_sha):
        raise ValueError("target_sha must be an exact lowercase 40-character commit SHA")
    if not _SHA1_RE.fullmatch(failure.source_sha):
        raise ValueError("failure.source_sha must be an exact lowercase 40-character commit SHA")
    if not isinstance(failure.failure_fingerprint, str) or not _SHA256_RE.fullmatch(failure.failure_fingerprint):
        raise ValueError("failure_fingerprint must be an exact lowercase 64-character SHA-256")

    workers = bounded_worker_matrix(worker_values, maximum=maximum_workers)
    kind = _kind_name(failure.kind)

    if kind == "INTEGRITY_FAILURE":
        probes = (ProbeFamily.DIRECT,)
    elif kind == "CODE_DEFECT":
        probes = (ProbeFamily.DIRECT, ProbeFamily.SHELL)
    elif kind == "TRANSIENT":
        probes = (ProbeFamily.DIRECT, ProbeFamily.PLATFORM)
    else:
        probes = (ProbeFamily.DIRECT, ProbeFamily.SHELL, ProbeFamily.PLATFORM)

    return ReconForensicPlan(
        target_sha=target_sha,
        source_sha=failure.source_sha,
        failure_fingerprint=failure.failure_fingerprint,
        kind=kind,
        probes=probes,
        worker_matrix=workers,
        auto_execute=False,
    )
