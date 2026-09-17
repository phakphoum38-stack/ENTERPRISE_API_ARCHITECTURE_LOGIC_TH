"""Failure ingestion boundary for RECON.

Captures deterministic failure identity and maps it to an adaptive RECON state.
This module records/normalizes observations only; it never grants authority,
changes governance, or mutates source.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re

from .autobot_governance import ReconState

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_TEXT = 2048


class FailureKind(str, Enum):
    CODE_DEFECT = "CODE_DEFECT"
    TRANSIENT = "TRANSIENT"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ReconFailure:
    source_sha: str
    gate: str
    test: str
    error_class: str
    message: str
    kind: FailureKind
    fingerprint: str
    state: ReconState


def ingest_failure(*, source_sha: str, gate: str, test: str, error_class: str, message: str, integrity_signal: bool = False) -> ReconFailure:
    _validate_sha(source_sha)
    for name, value in (("gate", gate), ("test", test), ("error_class", error_class), ("message", message)):
        if not isinstance(value, str) or not value.strip() or len(value) > _MAX_TEXT:
            raise ValueError(f"invalid_{name}")

    if integrity_signal:
        kind = FailureKind.INTEGRITY_FAILURE
        state = ReconState.INTEGRITY_FAILURE
    elif error_class in {"ModuleNotFoundError", "ImportError", "SyntaxError", "TypeError", "NameError", "AssertionError"}:
        kind = FailureKind.CODE_DEFECT
        state = ReconState.CODE_DEFECT
    elif error_class in {"TimeoutError", "ConnectionError"}:
        kind = FailureKind.TRANSIENT
        state = ReconState.WAITING
    else:
        kind = FailureKind.UNKNOWN
        state = ReconState.FAIL

    material = {
        "source_sha": source_sha,
        "gate": gate,
        "test": test,
        "error_class": error_class,
        "message": message,
        "kind": kind.value,
    }
    fingerprint = hashlib.sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ReconFailure(source_sha, gate, test, error_class, message, kind, fingerprint, state)


def _validate_sha(value: str) -> None:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise ValueError("source_sha must be a 40-character lowercase commit SHA")
