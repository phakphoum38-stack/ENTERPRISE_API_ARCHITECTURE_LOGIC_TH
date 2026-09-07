"""Fail-closed verification contract for Autobot repair results."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from typing import Any, Mapping

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MAX_TEXT = 2048
_MAX_PAYLOAD = 64 * 1024
_BLOCKED_KEYS = re.compile(
    r"(?:secret|token|password|private.?key|api.?key|credential|approval|authorize|release|merge|dispatch|shell|process|subprocess|mcp|computer.?use|exec|eval)",
    re.IGNORECASE,
)
_BLOCKED_VALUES = re.compile(
    r"(?:BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_[A-Za-z0-9_\-]+|sk-proj-[A-Za-z0-9_\-]+|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess)",
    re.IGNORECASE,
)


class RepairVerificationError(ValueError):
    """Raised when repair verification cannot be established safely."""


class VerificationState(str, Enum):
    PENDING = "PENDING"
    VERIFYING = "VERIFYING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class RepairVerification:
    source_sha: str
    repair_sha: str
    correlation_id: str
    ci_status: str
    evidence: Mapping[str, Any]
    provenance_fingerprint: str | None = None
    state: VerificationState = VerificationState.PENDING

    def __post_init__(self) -> None:
        _sha(self.source_sha, "source_sha")
        _sha(self.repair_sha, "repair_sha")
        if self.source_sha == self.repair_sha:
            raise RepairVerificationError("repair SHA must differ from source SHA")
        _text(self.correlation_id, "correlation_id")
        _text(self.ci_status, "ci_status")
        if self.provenance_fingerprint is not None:
            if not re.fullmatch(r"[0-9a-f]{64}", self.provenance_fingerprint):
                raise RepairVerificationError("invalid provenance fingerprint")
        clean = _sanitize(self.evidence, "evidence")
        object.__setattr__(self, "evidence", clean)
        if self.state is VerificationState.PASSED:
            if self.ci_status != "PASS":
                raise RepairVerificationError("PASSED requires PASS CI status")
            if clean.get("status") != "PASS":
                raise RepairVerificationError("PASSED requires explicit PASS evidence")
            if clean.get("commit_sha") != self.repair_sha:
                raise RepairVerificationError("PASSED requires matching repair SHA")
            if clean.get("correlation_id") != self.correlation_id:
                raise RepairVerificationError("PASSED requires matching correlation")
            if self.provenance_fingerprint is None:
                raise RepairVerificationError("PASSED requires provenance fingerprint")

    def verified_ci_pass(self) -> "RepairVerification":
        status = self.evidence.get("status")
        evidence_sha = self.evidence.get("commit_sha")
        evidence_corr = self.evidence.get("correlation_id")
        if status != "PASS":
            raise RepairVerificationError("explicit CI PASS evidence is required")
        if evidence_sha != self.repair_sha:
            raise RepairVerificationError("CI evidence SHA does not match repair SHA")
        if evidence_corr != self.correlation_id:
            raise RepairVerificationError("CI evidence correlation does not match")
        if self.provenance_fingerprint is None:
            raise RepairVerificationError("provenance fingerprint is required")
        return RepairVerification(
            source_sha=self.source_sha,
            repair_sha=self.repair_sha,
            correlation_id=self.correlation_id,
            ci_status="PASS",
            evidence=dict(self.evidence),
            provenance_fingerprint=self.provenance_fingerprint,
            state=VerificationState.PASSED,
        )._finalize()

    def _finalize(self) -> "RepairVerification":
        object.__setattr__(self, "evidence", _sanitize(self.evidence, "evidence"))
        return self

    @property
    def fingerprint(self) -> str:
        material = {
            "source_sha": self.source_sha,
            "repair_sha": self.repair_sha,
            "correlation_id": self.correlation_id,
            "ci_status": self.ci_status,
            "evidence": self.evidence,
            "provenance_fingerprint": self.provenance_fingerprint,
            "state": self.state.value,
        }
        return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def verify_repair_evidence(
    *, source_sha: str, repair_sha: str, correlation_id: str, evidence: Mapping[str, Any], provenance_fingerprint: str | None
) -> RepairVerification:
    record = RepairVerification(
        source_sha=source_sha,
        repair_sha=repair_sha,
        correlation_id=correlation_id,
        ci_status=str(evidence.get("status", "UNKNOWN")),
        evidence=evidence,
        provenance_fingerprint=provenance_fingerprint,
        state=VerificationState.VERIFYING,
    )
    if evidence.get("status") == "PASS":
        return record.verified_ci_pass()
    return RepairVerification(
        source_sha=source_sha,
        repair_sha=repair_sha,
        correlation_id=correlation_id,
        ci_status=record.ci_status,
        evidence=dict(record.evidence),
        provenance_fingerprint=record.provenance_fingerprint,
        state=VerificationState.FAILED if evidence.get("status") == "FAIL" else VerificationState.BLOCKED,
    )


def _sha(value: str, name: str) -> None:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise RepairVerificationError(f"{name} must be a valid lowercase commit SHA")


def _text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value or len(value) > _MAX_TEXT:
        raise RepairVerificationError(f"{name} must be bounded text")


def _sanitize(value: Any, name: str, depth: int = 0) -> Any:
    if depth > 6:
        raise RepairVerificationError(f"{name} exceeds maximum depth")
    if isinstance(value, Mapping):
        result = {}
        for key, item in value.items():
            if not isinstance(key, str) or _BLOCKED_KEYS.search(key):
                raise RepairVerificationError("blocked evidence key")
            result[key] = _sanitize(item, name, depth + 1)
        clean = result
    elif isinstance(value, (list, tuple)):
        if len(value) > 128:
            raise RepairVerificationError("evidence list exceeds bound")
        clean = [_sanitize(item, name, depth + 1) for item in value]
    elif isinstance(value, str):
        if len(value) > _MAX_TEXT or _BLOCKED_VALUES.search(value):
            raise RepairVerificationError("blocked evidence value")
        clean = value
    elif value is None or isinstance(value, (bool, int, float)):
        clean = value
    else:
        raise RepairVerificationError("unsupported evidence value")
    if len(json.dumps(clean, separators=(",", ":"), ensure_ascii=False).encode("utf-8")) > _MAX_PAYLOAD:
        raise RepairVerificationError("evidence exceeds payload bound")
    return clean
