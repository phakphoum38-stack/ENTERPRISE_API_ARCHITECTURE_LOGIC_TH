"""Fail-closed, side-effect-free Mission Control desktop projection for H3."""

from __future__ import annotations

import copy
import json
import re
from collections.abc import Mapping
from typing import Any

from .evidence_provenance import EvidenceRecord, ProvenanceChain, validate_freshness


class MissionControlDesktopError(ValueError):
    """Raised when desktop presentation data is unsafe or stale."""


class MissionControlDesktopContract:
    """Convert validated H2 evidence into bounded read-only desktop data."""

    SCHEMA = "research-os-mission-control-desktop/v1"
    MAX_BYTES = 64 * 1024
    MAX_TEXT = 2048
    MAX_SUMMARY_ITEMS = 64
    MAX_SUMMARY_DEPTH = 6
    STATUSES = frozenset({"PASS", "FAIL", "PENDING", "UNKNOWN", "BLOCKED"})
    BLOCKED_KEYS = re.compile(
        r"(?:approval|approve|authorize|permission|release|merge|dispatch|"
        r"credential|secret|token|password|private.?key|api.?key|callback|callable|"
        r"function|lambda|eval|exec|shell|command|process|subprocess|"
        r"computer.?use|mcp)",
        re.I,
    )
    BLOCKED_VALUES = re.compile(
        r"(?:BEGIN PRIVATE KEY|ghp_|sk-proj-|javascript:|data:text/html|"
        r"powershell|cmd\.exe|bash\s+-c|os\.system|child_process)",
        re.I,
    )

    def project(
        self,
        record: EvidenceRecord,
        *,
        owner_id: str,
        expected_sha: str,
        current_correlation_id: str,
        provenance: ProvenanceChain | None = None,
        status: str = "UNKNOWN",
        summary: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        self._bounded_text(owner_id, "owner_id")
        if status not in self.STATUSES:
            raise MissionControlDesktopError("unknown desktop status must remain UNKNOWN")
        if not validate_freshness(record, expected_sha=expected_sha, current_correlation_id=current_correlation_id):
            raise MissionControlDesktopError("evidence identity or correlation is stale")
        if provenance is not None:
            try:
                if provenance.source_sha != expected_sha:
                    raise MissionControlDesktopError("provenance source SHA mismatch")
                if not provenance.records or provenance.records[-1].fingerprint != record.fingerprint:
                    raise MissionControlDesktopError("provenance does not terminate at evidence record")
            except (AttributeError, IndexError) as exc:
                raise MissionControlDesktopError("malformed provenance") from exc

        clean_summary = self._sanitize_mapping(summary or {})
        result: dict[str, Any] = {
            "schema": self.SCHEMA,
            "owner_id": owner_id,
            "read_only": True,
            "source_sha": record.source_sha,
            "correlation_id": record.correlation_id,
            "evidence_type": record.evidence_type,
            "status": status,
            "provenance_fingerprint": provenance.fingerprint if provenance else record.fingerprint,
            "summary": clean_summary,
            "truncated": False,
        }
        if record.artifact_sha256 is not None:
            result["artifact_sha256"] = record.artifact_sha256
        self._validate_output(result, owner_id, expected_sha, current_correlation_id)
        return copy.deepcopy(result)

    def _validate_output(self, value: Mapping[str, Any], owner_id: str, expected_sha: str, correlation_id: str) -> None:
        if value.get("schema") != self.SCHEMA or value.get("owner_id") != owner_id:
            raise MissionControlDesktopError("invalid desktop identity")
        if value.get("read_only") is not True:
            raise MissionControlDesktopError("desktop contract must be read-only")
        if value.get("source_sha") != expected_sha or value.get("correlation_id") != correlation_id:
            raise MissionControlDesktopError("desktop identity binding failed")
        self._walk_safe(value)
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        if len(encoded) > self.MAX_BYTES:
            raise MissionControlDesktopError("desktop projection exceeds byte bound")

    def _sanitize_mapping(self, value: Mapping[str, Any]) -> dict[str, Any]:
        if not isinstance(value, Mapping):
            raise MissionControlDesktopError("summary must be an object")
        sanitized = self._sanitize_value(value, depth=0)
        if not isinstance(sanitized, dict):
            raise MissionControlDesktopError("summary must remain an object")
        return sanitized

    def _sanitize_value(self, value: Any, *, depth: int) -> Any:
        if depth > self.MAX_SUMMARY_DEPTH:
            raise MissionControlDesktopError("summary nesting exceeds bound")
        if isinstance(value, Mapping):
            if len(value) > self.MAX_SUMMARY_ITEMS:
                raise MissionControlDesktopError("summary mapping exceeds bound")
            result: dict[str, Any] = {}
            for key, child in value.items():
                if not isinstance(key, str) or len(key) > self.MAX_TEXT:
                    raise MissionControlDesktopError("invalid summary key")
                if self.BLOCKED_KEYS.search(key):
                    raise MissionControlDesktopError(f"blocked summary key: {key}")
                result[key] = self._sanitize_value(child, depth=depth + 1)
            return result
        if isinstance(value, (list, tuple)):
            if len(value) > self.MAX_SUMMARY_ITEMS:
                raise MissionControlDesktopError("summary collection exceeds bound")
            return [self._sanitize_value(item, depth=depth + 1) for item in value]
        if isinstance(value, str):
            if len(value) > self.MAX_TEXT or self.BLOCKED_VALUES.search(value):
                raise MissionControlDesktopError("blocked or oversized summary value")
            return value
        if value is None or isinstance(value, (bool, int, float)):
            return value
        raise MissionControlDesktopError(f"unsupported summary type: {type(value).__name__}")

    def _walk_safe(self, value: Any, *, depth: int = 0) -> None:
        if depth > self.MAX_SUMMARY_DEPTH:
            raise MissionControlDesktopError("desktop payload nesting exceeds bound")
        if isinstance(value, Mapping):
            for key, child in value.items():
                if not isinstance(key, str) or self.BLOCKED_KEYS.search(key):
                    raise MissionControlDesktopError("desktop payload contains forbidden field")
                self._walk_safe(child, depth=depth + 1)
        elif isinstance(value, list):
            if len(value) > self.MAX_SUMMARY_ITEMS:
                raise MissionControlDesktopError("desktop collection exceeds bound")
            for child in value:
                self._walk_safe(child, depth=depth + 1)
        elif isinstance(value, str):
            if len(value) > self.MAX_TEXT or self.BLOCKED_VALUES.search(value):
                raise MissionControlDesktopError("desktop payload contains forbidden value")
        elif value is None or isinstance(value, (bool, int, float)):
            return
        else:
            raise MissionControlDesktopError("desktop payload contains dynamic value")

    def _bounded_text(self, value: str, name: str) -> None:
        if not isinstance(value, str) or not value or len(value) > self.MAX_TEXT:
            raise MissionControlDesktopError(f"{name} is invalid or oversized")
