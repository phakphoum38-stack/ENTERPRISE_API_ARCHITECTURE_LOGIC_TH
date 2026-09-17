"""Canonical identity federation for governed AEOS execution planes.

This module is intentionally side-effect free. It does not dispatch work,
mutate queues, grant authority, or change Git refs. It provides one immutable
identity envelope that adapters can use to correlate existing AEOS, RECON,
Forensic, API, V3, Friend, resource-control, evidence, and artifact records.

Identity hierarchy:
    mission -> work -> task -> run -> attempt

Cross-plane bindings:
    request -> admission
    evidence/artifact/decision bind to the execution lineage

Attempt semantics are deliberately represented but not interpreted here;
P0-2 owns retry/attempt lifecycle rules.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import re
from typing import Any, Mapping


_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class CanonicalIdentityError(ValueError):
    """Raised when canonical identity federation invariants are violated."""


def _required(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CanonicalIdentityError(f"{name} must be a non-empty string")
    return value.strip()


def _optional(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    return _required(value, name)


def _sha(value: str, name: str = "baseline_sha") -> str:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise CanonicalIdentityError(
            f"{name} must be a 40-character lowercase commit SHA"
        )
    return value


@dataclass(frozen=True)
class CanonicalIdentity:
    """Immutable cross-plane identity envelope.

    The envelope deliberately does not replace any existing runtime identity.
    Existing IDs remain authoritative inside their native plane; these fields
    provide the canonical correlation contract between planes.
    """

    mission_id: str
    work_id: str
    baseline_sha: str
    task_id: str | None = None
    run_id: str | None = None
    attempt_id: str | None = None
    request_id: str | None = None
    admission_id: str | None = None
    evidence_id: str | None = None
    artifact_id: str | None = None
    decision_id: str | None = None

    def __post_init__(self) -> None:
        _required(self.mission_id, "mission_id")
        _required(self.work_id, "work_id")
        _sha(self.baseline_sha)

        values = (
            ("task_id", self.task_id),
            ("run_id", self.run_id),
            ("attempt_id", self.attempt_id),
            ("request_id", self.request_id),
            ("admission_id", self.admission_id),
            ("evidence_id", self.evidence_id),
            ("artifact_id", self.artifact_id),
            ("decision_id", self.decision_id),
        )
        for name, value in values:
            _optional(value, name)

        if self.task_id is None and any(
            value is not None
            for value in (
                self.run_id,
                self.attempt_id,
                self.request_id,
                self.admission_id,
            )
        ):
            raise CanonicalIdentityError(
                "task_id is required before run/attempt/request/admission identity"
            )
        if self.run_id is None and any(
            value is not None
            for value in (self.attempt_id, self.request_id, self.admission_id)
        ):
            raise CanonicalIdentityError(
                "run_id is required before attempt/request/admission identity"
            )
        if self.attempt_id is None and self.admission_id is not None:
            raise CanonicalIdentityError(
                "attempt_id is required before admission identity"
            )
        if self.request_id is None and self.admission_id is not None:
            raise CanonicalIdentityError(
                "request_id is required before admission identity"
            )
        if self.run_id is None and any(
            value is not None for value in (self.evidence_id, self.artifact_id)
        ):
            raise CanonicalIdentityError(
                "run_id is required before evidence/artifact identity"
            )
        if self.evidence_id is None and self.artifact_id is not None:
            raise CanonicalIdentityError(
                "evidence_id is required before artifact identity"
            )

    def bind(self, **updates: str | None) -> "CanonicalIdentity":
        """Return a new identity with additional cross-plane bindings."""

        allowed = {
            "task_id",
            "run_id",
            "attempt_id",
            "request_id",
            "admission_id",
            "evidence_id",
            "artifact_id",
            "decision_id",
        }
        unknown = set(updates) - allowed
        if unknown:
            raise CanonicalIdentityError(
                f"unsupported identity fields: {sorted(unknown)}"
            )
        return replace(self, **updates)

    def as_mapping(self) -> dict[str, str | None]:
        return {
            "mission_id": self.mission_id,
            "work_id": self.work_id,
            "task_id": self.task_id,
            "run_id": self.run_id,
            "attempt_id": self.attempt_id,
            "request_id": self.request_id,
            "admission_id": self.admission_id,
            "evidence_id": self.evidence_id,
            "artifact_id": self.artifact_id,
            "decision_id": self.decision_id,
            "baseline_sha": self.baseline_sha,
        }

    def fingerprint(self) -> str:
        """Return a deterministic SHA-256 fingerprint of the envelope."""

        material = json.dumps(
            self.as_mapping(),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(material).hexdigest()


def identity_from_work_item(work_item: Any) -> CanonicalIdentity:
    """Federate an existing AEOS WorkItem without replacing it."""

    return CanonicalIdentity(
        mission_id=_required(work_item.mission_id, "mission_id"),
        work_id=_required(work_item.work_id, "work_id"),
        baseline_sha=_sha(work_item.baseline_sha),
    )


def identity_from_mapping(
    record: Mapping[str, Any],
    *,
    mission_key: str = "mission_id",
    work_key: str = "work_id",
    baseline_key: str = "baseline_sha",
) -> CanonicalIdentity:
    """Federate an existing plane record using explicit field names.

    This is an adapter boundary only: callers remain responsible for proving
    that the source record itself is authoritative.
    """

    return CanonicalIdentity(
        mission_id=_required(record.get(mission_key), mission_key),
        work_id=_required(record.get(work_key), work_key),
        baseline_sha=_sha(record.get(baseline_key), baseline_key),
        task_id=record.get("task_id"),
        run_id=record.get("run_id"),
        attempt_id=record.get("attempt_id"),
        request_id=record.get("request_id"),
        admission_id=record.get("admission_id"),
        evidence_id=record.get("evidence_id"),
        artifact_id=record.get("artifact_id"),
        decision_id=record.get("decision_id"),
    )


def assert_same_lineage(left: CanonicalIdentity, right: CanonicalIdentity) -> None:
    """Fail closed when two records cannot belong to the same work lineage."""

    if left.mission_id != right.mission_id:
        raise CanonicalIdentityError("mission_id lineage conflict")
    if left.work_id != right.work_id:
        raise CanonicalIdentityError("work_id lineage conflict")
    if left.baseline_sha != right.baseline_sha:
        raise CanonicalIdentityError("baseline_sha lineage conflict")
