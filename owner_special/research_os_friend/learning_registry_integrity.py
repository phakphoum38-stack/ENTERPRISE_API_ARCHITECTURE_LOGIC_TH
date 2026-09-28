"""Bounded immutable registry for evidence-backed learned skills."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any

_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_FP_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOCKED = re.compile(
    r"(?:secret|token|password|private.?key|api.?key|credential|approval|authorize|release|merge|dispatch|shell|process|subprocess|mcp|computer.?use|exec|eval)",
    re.I,
)
_BLOCKED_VALUE = re.compile(
    r"(?:BEGIN [A-Z ]*PRIVATE KEY|gh[pousr]_|sk-proj-|javascript:|data:text/html|powershell|cmd(?:\.exe)?|bash -c|os\.system|subprocess)",
    re.I,
)


class LearningRegistryError(ValueError):
    """Raised when a registry entry violates integrity or safety bounds."""


@dataclass(frozen=True)
class LearningRegistryEntry:
    owner: str
    source_sha: str
    correlation_id: str
    name: str
    goal: str
    evidence_fingerprint: str
    promotion_fingerprint: str
    version: int = 1

    def __post_init__(self) -> None:
        if not isinstance(self.owner, str) or not self.owner or len(self.owner) > 256:
            raise LearningRegistryError("owner must be bounded")
        if not isinstance(self.source_sha, str) or not _SHA_RE.fullmatch(self.source_sha):
            raise LearningRegistryError("invalid source SHA")
        if not isinstance(self.correlation_id, str) or not self.correlation_id or len(self.correlation_id) > 256:
            raise LearningRegistryError("invalid correlation id")
        for value, label in ((self.name, "name"), (self.goal, "goal")):
            if not isinstance(value, str) or not value or len(value) > 2048 or _BLOCKED.search(value) or _BLOCKED_VALUE.search(value):
                raise LearningRegistryError(f"unsafe {label}")
        for value, label in ((self.evidence_fingerprint, "evidence fingerprint"), (self.promotion_fingerprint, "promotion fingerprint")):
            if not isinstance(value, str) or not _FP_RE.fullmatch(value):
                raise LearningRegistryError(f"invalid {label}")
        if not isinstance(self.version, int) or isinstance(self.version, bool) or not 1 <= self.version <= 100:
            raise LearningRegistryError("invalid registry version")

    @property
    def fingerprint(self) -> str:
        material = {
            "owner": self.owner,
            "source_sha": self.source_sha,
            "correlation_id": self.correlation_id,
            "name": self.name,
            "goal": self.goal,
            "evidence_fingerprint": self.evidence_fingerprint,
            "promotion_fingerprint": self.promotion_fingerprint,
            "version": self.version,
        }
        return hashlib.sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class LearningRegistry:
    """In-memory bounded registry; persistence and execution remain outside this contract."""

    MAX_ENTRIES = 128

    def __init__(self) -> None:
        self._entries: dict[str, LearningRegistryEntry] = {}

    def add(self, entry: LearningRegistryEntry) -> LearningRegistryEntry:
        existing = self._entries.get(entry.fingerprint)
        if existing is not None:
            if existing != entry:
                raise LearningRegistryError("conflicting duplicate fingerprint")
            return existing
        if len(self._entries) >= self.MAX_ENTRIES:
            raise LearningRegistryError("registry capacity exceeded")
        if any(existing_entry.owner == entry.owner and existing_entry.name == entry.name and existing_entry.version == entry.version and existing_entry.fingerprint != entry.fingerprint for existing_entry in self._entries.values()):
            raise LearningRegistryError("conflicting registry version")
        self._entries[entry.fingerprint] = entry
        return entry

    def snapshot(self) -> dict[str, Any]:
        entries = [
            {
                "owner": entry.owner,
                "source_sha": entry.source_sha,
                "correlation_id": entry.correlation_id,
                "name": entry.name,
                "goal": entry.goal,
                "evidence_fingerprint": entry.evidence_fingerprint,
                "promotion_fingerprint": entry.promotion_fingerprint,
                "version": entry.version,
                "fingerprint": entry.fingerprint,
            }
            for entry in self._entries.values()
        ]
        entries.sort(key=lambda item: (item["owner"], item["name"], item["version"], item["fingerprint"]))
        return {"schema": "research-os-learning-registry/v1", "read_only": True, "authority": "none", "entries": entries}
