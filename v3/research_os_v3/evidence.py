from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
from typing import Iterable


@dataclass(frozen=True)
class Evidence:
    id: str
    claim: str
    source_uri: str
    excerpt: str = ""
    task_id: str | None = None
    artifact_id: str | None = None
    confidence: float = 0.0
    metadata: dict[str, str] = field(default_factory=dict)
    captured_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def __post_init__(self) -> None:
        if not self.claim.strip():
            raise ValueError("claim must not be empty")
        if not self.source_uri.strip():
            raise ValueError("source_uri must not be empty")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


class EvidenceStore:
    """In-memory evidence boundary used by the domain layer.

    Persistence adapters can implement the same semantics later without
    changing the research planner or synthesis layer.
    """

    def __init__(self) -> None:
        self._items: dict[str, Evidence] = {}

    def add(self, evidence: Evidence) -> Evidence:
        if evidence.id in self._items:
            raise ValueError(f"evidence already exists: {evidence.id}")
        self._items[evidence.id] = evidence
        return evidence

    def get(self, evidence_id: str) -> Evidence | None:
        return self._items.get(evidence_id)

    def for_task(self, task_id: str) -> tuple[Evidence, ...]:
        return tuple(item for item in self._items.values() if item.task_id == task_id)

    def all(self) -> tuple[Evidence, ...]:
        return tuple(self._items.values())

    def claims(self) -> tuple[str, ...]:
        seen: set[str] = set()
        result: list[str] = []
        for item in self._items.values():
            key = item.claim.strip().casefold()
            if key not in seen:
                seen.add(key)
                result.append(item.claim)
        return tuple(result)


def evidence_id(claim: str, source_uri: str, excerpt: str = "") -> str:
    payload = "\x1f".join((claim.strip(), source_uri.strip(), excerpt.strip()))
    return "evidence-" + sha256(payload.encode("utf-8")).hexdigest()[:16]


def merge_evidence(*groups: Iterable[Evidence]) -> tuple[Evidence, ...]:
    merged: dict[str, Evidence] = {}
    for group in groups:
        for item in group:
            merged[item.id] = item
    return tuple(merged.values())
