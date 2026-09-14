#!/usr/bin/env python3
"""Universal AEOS failure intake, normalization, and causal consolidation.

This layer accepts failures from any assurance surface (H00-H27, CI, tests,
contracts, artifacts, provenance, security, runtime, or authority), normalizes
identity/evidence, collapses duplicates by declared root cause, and emits one
bounded repair batch. It never mutates source, grants authority, or merges.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Iterable


class UniversalFailureError(ValueError):
    """Raised when a failure record is unsafe or incomplete."""


@dataclass(frozen=True)
class FailureRecord:
    failure_id: str
    scope: str
    dimension: str
    status: str
    symptom: str
    evidence_ref: str
    source_sha: str
    root_cause: str | None = None
    severity: str = "P1"
    blocking: bool = True
    repair_required: bool = True
    verification_required: bool = True

    def validate(self, expected_source_sha: str) -> None:
        if not self.failure_id or not self.scope or not self.dimension or not self.status:
            raise UniversalFailureError("FAILURE_RECORD_INCOMPLETE")
        if not self.evidence_ref:
            raise UniversalFailureError("EVIDENCE_MISSING")
        if len(self.source_sha) != 40 or any(c not in "0123456789abcdef" for c in self.source_sha):
            raise UniversalFailureError("IDENTITY_MISMATCH")
        if self.source_sha != expected_source_sha:
            raise UniversalFailureError("STALE_FAILURE_SOURCE")
        if self.status != "PASS" and not self.root_cause:
            raise UniversalFailureError("ROOT_CAUSE_UNKNOWN")

    @property
    def fingerprint(self) -> str:
        value = {
            "scope": self.scope,
            "dimension": self.dimension,
            "status": self.status,
            "symptom": self.symptom,
            "root_cause": self.root_cause,
        }
        return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def normalize_failures(records: Iterable[FailureRecord], source_sha: str) -> tuple[FailureRecord, ...]:
    items = tuple(records)
    for record in items:
        record.validate(source_sha)
    return items


def collapse_failures(records: Iterable[FailureRecord], source_sha: str) -> dict[str, tuple[FailureRecord, ...]]:
    items = normalize_failures(records, source_sha)
    groups: dict[str, list[FailureRecord]] = {}
    for record in items:
        if record.status == "PASS":
            continue
        assert record.root_cause is not None
        groups.setdefault(record.root_cause, []).append(record)
    return {root: tuple(groups[root]) for root in sorted(groups)}


def build_universal_repair_batch(records: Iterable[FailureRecord], source_sha: str) -> tuple[str, ...]:
    groups = collapse_failures(records, source_sha)
    roots = tuple(groups)
    if any(record.repair_required and not record.verification_required for group in groups.values() for record in group):
        raise UniversalFailureError("VERIFICATION_REQUIREMENT_MISSING")
    return roots


def completion_ready(records: Iterable[FailureRecord], source_sha: str) -> bool:
    items = normalize_failures(records, source_sha)
    return bool(items) and all(record.status == "PASS" for record in items)
