"""Fail-closed evidence and provenance primitives for Research OS H2.

This module is intentionally side-effect free. CI remains the producer of
runtime/generated evidence and release authority remains outside this module.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, Mapping

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_TEXT = 2048
_MAX_PAYLOAD_BYTES = 64 * 1024
_MAX_CHAIN = 64
_SECRET_KEYS = frozenset({"password", "passwd", "secret", "token", "api_key", "apikey", "private_key"})
_AUTHORITY_KEYS = frozenset({"approve", "approved", "release", "merge", "dispatch", "authorize", "permission_grant"})


class ProvenanceError(ValueError):
    """Raised when evidence cannot be trusted or safely consumed."""


@dataclass(frozen=True)
class EvidenceRecord:
    """Immutable, bounded evidence bound to one exact source SHA."""

    schema: str
    evidence_type: str
    source_sha: str
    producer: str
    correlation_id: str
    observed_at: str
    payload: Mapping[str, Any]
    artifact_sha256: str | None = None
    parent_fingerprint: str | None = None

    def __post_init__(self) -> None:
        _validate_sha(self.source_sha, "source_sha")
        for name, value in (
            ("schema", self.schema),
            ("evidence_type", self.evidence_type),
            ("producer", self.producer),
            ("correlation_id", self.correlation_id),
            ("observed_at", self.observed_at),
        ):
            _bounded_text(value, name)
        if self.artifact_sha256 is not None and not _DIGEST_RE.fullmatch(self.artifact_sha256):
            raise ProvenanceError("artifact_sha256 must be a 64-character lowercase SHA-256 digest")
        if self.parent_fingerprint is not None and not _DIGEST_RE.fullmatch(self.parent_fingerprint):
            raise ProvenanceError("parent_fingerprint must be a SHA-256 digest")
        frozen = _validate_payload(self.payload)
        object.__setattr__(self, "payload", MappingProxyType(frozen))

    @property
    def fingerprint(self) -> str:
        material = {
            "schema": self.schema,
            "evidence_type": self.evidence_type,
            "source_sha": self.source_sha,
            "producer": self.producer,
            "correlation_id": self.correlation_id,
            "observed_at": self.observed_at,
            "payload": self.payload,
            "artifact_sha256": self.artifact_sha256,
            "parent_fingerprint": self.parent_fingerprint,
        }
        encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class ProvenanceChain:
    """Ordered evidence chain with one immutable source identity."""

    records: tuple[EvidenceRecord, ...]

    def __post_init__(self) -> None:
        if not self.records or len(self.records) > _MAX_CHAIN:
            raise ProvenanceError("provenance chain must be non-empty and bounded")
        source_sha = self.records[0].source_sha
        for index, record in enumerate(self.records):
            if record.source_sha != source_sha:
                raise ProvenanceError("conflicting source SHA in provenance chain")
            if index and record.parent_fingerprint != self.records[index - 1].fingerprint:
                raise ProvenanceError("broken parent fingerprint in provenance chain")

    @property
    def source_sha(self) -> str:
        return self.records[0].source_sha

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(
            "|".join(record.fingerprint for record in self.records).encode("ascii")
        ).hexdigest()

    def append(self, record: EvidenceRecord) -> "ProvenanceChain":
        if record.source_sha != self.source_sha:
            raise ProvenanceError("cannot append evidence from a different source SHA")
        linked = EvidenceRecord(
            schema=record.schema,
            evidence_type=record.evidence_type,
            source_sha=record.source_sha,
            producer=record.producer,
            correlation_id=record.correlation_id,
            observed_at=record.observed_at,
            payload=record.payload,
            artifact_sha256=record.artifact_sha256,
            parent_fingerprint=self.records[-1].fingerprint,
        )
        return ProvenanceChain(self.records + (linked,))


def validate_freshness(record: EvidenceRecord, *, expected_sha: str, current_correlation_id: str) -> bool:
    """Return False rather than guessing when identity or correlation is stale."""
    if not _SHA_RE.fullmatch(expected_sha):
        return False
    if not isinstance(current_correlation_id, str) or not current_correlation_id:
        return False
    return record.source_sha == expected_sha and record.correlation_id == current_correlation_id


def validate_evidence_authority(payload: Mapping[str, Any]) -> None:
    """Reject evidence payloads that attempt to become an authority channel."""
    if not isinstance(payload, Mapping):
        raise ProvenanceError("evidence payload must be a mapping")
    _reject_authority_keys(payload)


def _validate_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ProvenanceError("payload must be a mapping")
    validate_evidence_authority(payload)
    sanitized = _sanitize_value(payload)
    if not isinstance(sanitized, Mapping):
        raise ProvenanceError("evidence payload must be a mapping")
    encoded = json.dumps(sanitized, sort_keys=True, separators=(",", ":"), default=_json_default).encode("utf-8")
    if len(encoded) > _MAX_PAYLOAD_BYTES:
        raise ProvenanceError("evidence payload exceeds size bound")
    return dict(sanitized)


def _reject_authority_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.lower() in _AUTHORITY_KEYS:
                raise ProvenanceError("evidence payload contains authority fields")
            _reject_authority_keys(child)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _reject_authority_keys(item)


def _sanitize_value(value: Any, *, key_name: str | None = None) -> Any:
    if key_name is not None and key_name.lower() in _SECRET_KEYS:
        raise ProvenanceError("secret-like evidence key rejected")
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, child in value.items():
            key_text = str(key)
            result[key_text] = _sanitize_value(child, key_name=key_text)
        return MappingProxyType(result)
    if isinstance(value, (list, tuple)):
        if len(value) > 128:
            raise ProvenanceError("evidence list exceeds size bound")
        return tuple(_sanitize_value(item) for item in value)
    if isinstance(value, str):
        if len(value) > _MAX_TEXT:
            raise ProvenanceError("evidence string exceeds size bound")
        if "BEGIN PRIVATE KEY" in value or "ghp_" in value or "sk-proj-" in value:
            raise ProvenanceError("secret-like evidence value rejected")
        return value
    if value is None or isinstance(value, (bool, int, float)):
        return value
    raise ProvenanceError(f"unsupported evidence value type: {type(value).__name__}")


def _validate_sha(value: str, name: str) -> None:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise ProvenanceError(f"{name} must be a 40-character lowercase commit SHA")


def _bounded_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value or len(value) > _MAX_TEXT:
        raise ProvenanceError(f"{name} must be non-empty and bounded")


def _json_default(value: Any) -> Any:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, (tuple, list)):
        return list(value)
    raise TypeError(f"not JSON serializable: {type(value).__name__}")
