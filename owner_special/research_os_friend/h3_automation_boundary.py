"""Fail-closed H3 Mission Control automation boundary.

This module is intentionally side-effect free. It validates a canonical
read-only Mission Control snapshot and produces a deterministic automation
assessment. It never dispatches workflows, mutates runtime state, approves,
releases, or merges.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from typing import Any


class H3AutomationBoundaryError(ValueError):
    """Raised when a Mission Control snapshot violates the H3 boundary."""


class H3AutomationBoundary:
    SCHEMA = "research-os-h3-mission-control-automation/v1"
    SNAPSHOT_SCHEMA = "research-os-mission-control-unified-snapshot/v1"
    H2_EVIDENCE_SCHEMA = "research-os-mission-control-evidence/v1"
    EVIDENCE_ATTESTATION_SCHEMA = "research-os-h3-evidence-attestation/v1"
    MAX_BYTES = 64 * 1024
    MAX_DEPTH = 8
    MAX_ITEMS = 100
    SHA_RE = re.compile(r"^[0-9a-f]{40}$")
    BLOCKED_KEYS = re.compile(
        r"(?:approve|release|merge|dispatch|authorize|permission|credential|secret|token|"
        r"private.?key|password|callback|callable|function|lambda|eval|exec|command|shell|"
        r"browser|mcp|computer.?use|process|mutation)", re.I
    )

    AUTHORITIES = {
        "execution_authority": "FriendOrchestrator",
        "authorization_authority": "OwnerPolicy",
        "approval_authority": "ApprovalGate",
    }

    def assess(self, snapshot: Mapping[str, Any], *, expected_sha: str, owner_id: str) -> dict[str, Any]:
        self._sha(expected_sha)
        if not isinstance(owner_id, str) or not owner_id.strip():
            raise H3AutomationBoundaryError("owner_id is required")
        if not isinstance(snapshot, Mapping):
            raise H3AutomationBoundaryError("snapshot must be an object")
        self._validate_snapshot(snapshot, expected_sha, owner_id)
        canonical = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        if len(canonical) > self.MAX_BYTES:
            raise H3AutomationBoundaryError("snapshot exceeds byte bound")
        return {
            "contract": self.SCHEMA,
            "source_sha": expected_sha,
            "owner_id": owner_id,
            "snapshot_fingerprint": hashlib.sha256(canonical).hexdigest(),
            "read_only": True,
            "auto_mode": "AUTO_GUARDED",
            "decision": "ALLOW_GUARDED_OBSERVATION",
            "authorities": dict(self.AUTHORITIES),
            "can_execute": False,
            "can_approve": False,
            "can_release": False,
            "can_merge": False,
            "can_dispatch": False,
        }

    def _validate_snapshot(self, snapshot: Mapping[str, Any], expected_sha: str, owner_id: str) -> None:
        if snapshot.get("schema") != self.SNAPSHOT_SCHEMA:
            raise H3AutomationBoundaryError("unsupported unified snapshot schema")
        if snapshot.get("owner_id") != owner_id:
            raise H3AutomationBoundaryError("snapshot owner mismatch")
        if snapshot.get("read_only") is not True:
            raise H3AutomationBoundaryError("snapshot must be read-only")
        for field, expected in self.AUTHORITIES.items():
            if snapshot.get(field) != expected:
                raise H3AutomationBoundaryError(f"invalid {field}")
        versions = snapshot.get("source_versions")
        if not isinstance(versions, Mapping):
            raise H3AutomationBoundaryError("source_versions is required")
        if versions.get("evidence") != self.H2_EVIDENCE_SCHEMA:
            raise H3AutomationBoundaryError("H2 evidence schema is not bound")
        self._validate_evidence_attestation(snapshot.get("evidence_verification"), expected_sha, owner_id)
        self._walk(snapshot, expected_sha, 0)

    def _validate_evidence_attestation(
        self, attestation: Any, expected_sha: str, owner_id: str
    ) -> None:
        if not isinstance(attestation, Mapping):
            raise H3AutomationBoundaryError("authoritative evidence verification is required")
        if attestation.get("schema") != self.EVIDENCE_ATTESTATION_SCHEMA:
            raise H3AutomationBoundaryError("unsupported evidence attestation schema")
        if attestation.get("status") != "PASS":
            raise H3AutomationBoundaryError("evidence verification must be PASS")
        if attestation.get("authoritative") is not True:
            raise H3AutomationBoundaryError("evidence verification is not authoritative")
        if attestation.get("owner_id") != owner_id:
            raise H3AutomationBoundaryError("evidence verification owner mismatch")
        if attestation.get("target_sha") != expected_sha:
            raise H3AutomationBoundaryError("evidence verification SHA does not match expected SHA")
        provenance = attestation.get("provenance")
        if not isinstance(provenance, Mapping):
            raise H3AutomationBoundaryError("evidence verification provenance is required")
        if provenance.get("exact_sha") != expected_sha:
            raise H3AutomationBoundaryError("evidence provenance SHA does not match expected SHA")
        if provenance.get("status") != "PASS":
            raise H3AutomationBoundaryError("evidence provenance must be PASS")
        if provenance.get("authoritative") is not True:
            raise H3AutomationBoundaryError("evidence provenance is not authoritative")

    def _walk(self, value: Any, expected_sha: str, depth: int) -> None:
        if depth > self.MAX_DEPTH:
            raise H3AutomationBoundaryError("payload nesting exceeds bound")
        if isinstance(value, Mapping):
            if len(value) > self.MAX_ITEMS:
                raise H3AutomationBoundaryError("mapping exceeds bound")
            for key, child in value.items():
                if not isinstance(key, str) or len(key) > 2048:
                    raise H3AutomationBoundaryError("invalid field name")
                if self.BLOCKED_KEYS.search(key) and key not in self.AUTHORITIES:
                    raise H3AutomationBoundaryError(f"blocked field: {key}")
                self._walk(child, expected_sha, depth + 1)
            if "source_sha" in value and value["source_sha"] != expected_sha:
                raise H3AutomationBoundaryError("stale or conflicting source SHA")
            if "target_sha" in value and value["target_sha"] != expected_sha:
                raise H3AutomationBoundaryError("stale or conflicting target SHA")
            if "exact_sha" in value and value["exact_sha"] != expected_sha:
                raise H3AutomationBoundaryError("stale or conflicting provenance SHA")
        elif isinstance(value, list):
            if len(value) > self.MAX_ITEMS:
                raise H3AutomationBoundaryError("collection exceeds bound")
            for child in value:
                self._walk(child, expected_sha, depth + 1)
        elif isinstance(value, str):
            if len(value) > 2048:
                raise H3AutomationBoundaryError("string exceeds bound")
        elif value is None or isinstance(value, (bool, int, float)):
            return
        else:
            raise H3AutomationBoundaryError("unsupported dynamic value")

    def _sha(self, value: str) -> None:
        if not isinstance(value, str) or not self.SHA_RE.fullmatch(value):
            raise H3AutomationBoundaryError("expected a canonical 40-character lowercase SHA")
