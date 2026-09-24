"""Canonical Phase B lifecycle/evidence boundary.

This module records the lifecycle around an existing executor. It never grants
authority and never executes the executor. Evidence is append-only JSONL,
fingerprint-bound, source-SHA-bound, and correlation-bound.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

LIFECYCLE = (
    "INTENT", "VALIDATE", "PREPARE", "AUTHORIZE", "EXECUTE",
    "OBSERVE", "EVIDENCE", "COMPLETE", "RECOVER",
)
TERMINAL = frozenset({"COMPLETE", "RECOVER"})


def _canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class LifecycleEvidence:
    event_id: str
    correlation_id: str
    capability_id: str
    action: str
    state: str
    owner_id: str
    source_sha: str
    target_sha: str
    workflow_run_id: str
    contract_version: str
    fingerprint: str
    timestamp: str
    evidence_sha256: str
    recovery_required: bool = False
    recovery_reason: str | None = None
    project_id: str = ""

    @classmethod
    def create(
        cls,
        *,
        correlation_id: str,
        capability_id: str,
        action: str,
        state: str,
        owner_id: str,
        source_sha: str,
        target_sha: str,
        workflow_run_id: str,
        contract_version: str = "research-os-canonical-platform/v1",
        recovery_required: bool = False,
        recovery_reason: str | None = None,
        project_id: str = "",
    ) -> "LifecycleEvidence":
        if state not in LIFECYCLE:
            raise ValueError(f"unknown lifecycle state: {state}")
        if not correlation_id or not owner_id or not source_sha or not target_sha:
            raise ValueError("identity, owner, source_sha and target_sha are required")
        if not workflow_run_id:
            raise ValueError("workflow_run_id is required")
        if recovery_required and not recovery_reason:
            raise ValueError("recovery_required requires recovery_reason")
        if project_id and not project_id.strip():
            raise ValueError("project_id cannot be blank")
        if state == "RECOVER" and not recovery_required:
            raise ValueError("RECOVER state requires recovery_required=true")
        core = {
            "correlation_id": correlation_id,
            "capability_id": capability_id,
            "action": action,
            "state": state,
            "owner_id": owner_id,
            "source_sha": source_sha,
            "target_sha": target_sha,
            "workflow_run_id": workflow_run_id,
            "contract_version": contract_version,
            "recovery_required": recovery_required,
            "recovery_reason": recovery_reason,
            "project_id": project_id,
        }
        fingerprint = _sha256(core)
        evidence_id = f"ev-{uuid.uuid4().hex}"
        timestamp = datetime.now(timezone.utc).isoformat()
        evidence_sha256 = _sha256({"event_id": evidence_id, "fingerprint": fingerprint, "timestamp": timestamp})
        return cls(
            event_id=evidence_id,
            correlation_id=correlation_id,
            capability_id=capability_id,
            action=action,
            state=state,
            owner_id=owner_id,
            source_sha=source_sha,
            target_sha=target_sha,
            workflow_run_id=workflow_run_id,
            contract_version=contract_version,
            fingerprint=fingerprint,
            timestamp=timestamp,
            evidence_sha256=evidence_sha256,
            recovery_required=recovery_required,
            recovery_reason=recovery_reason,
            project_id=project_id,
        )


class LifecycleEvidenceLedger:
    """Append-only evidence ledger for a single lifecycle correlation."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, record: LifecycleEvidence) -> None:
        if record.state == "RECOVER" and not record.recovery_required:
            raise ValueError("RECOVER state requires recovery_required=true")
        if record.recovery_required and not record.recovery_reason:
            raise ValueError("recovery_required requires recovery_reason")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as stream:
            stream.write(_canonical(asdict(record)) + "\n")

    def read(self) -> tuple[LifecycleEvidence, ...]:
        if not self.path.exists():
            return ()
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            payload = json.loads(line)
            records.append(LifecycleEvidence(**payload))
        return tuple(records)

    def validate_chain(
        self,
        *,
        correlation_id: str,
        expected_source_sha: str,
        expected_project_id: str | None = None,
    ) -> tuple[str, ...]:
        records = self.read()
        errors: list[str] = []
        if not records:
            return ("missing lifecycle evidence",)
        for record in records:
            if record.correlation_id != correlation_id:
                errors.append("correlation mismatch")
            if record.source_sha != expected_source_sha:
                errors.append("source SHA mismatch")
            if expected_project_id is not None and record.project_id != expected_project_id:
                errors.append("project identity mismatch")
            if record.state not in LIFECYCLE:
                errors.append("unknown lifecycle state")
            if record.recovery_required and not record.recovery_reason:
                errors.append("recovery reason missing")
        states = [record.state for record in records]
        if states[-1] not in TERMINAL:
            errors.append("lifecycle has no terminal recovery/complete state")
        if states[-1] == "COMPLETE" and any(record.recovery_required for record in records):
            errors.append("completed lifecycle cannot retain unresolved recovery")
        if any(state in TERMINAL for state in states[:-1]):
            errors.append("terminal lifecycle state cannot be followed")
        return tuple(errors)


def evidence_payload(record: LifecycleEvidence) -> Mapping[str, object]:
    """Return a serializable payload without adding execution authority."""
    return asdict(record)


__all__ = [
    "LIFECYCLE",
    "LifecycleEvidence",
    "LifecycleEvidenceLedger",
    "evidence_payload",
]
