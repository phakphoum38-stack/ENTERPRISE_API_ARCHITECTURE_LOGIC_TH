#!/usr/bin/env python3
"""Research OS AI Brain context assembly and recall ports.

The Context Engine converts multiple Research OS sources into a bounded,
secret-safe, provenance-aware snapshot. It is deterministic and model-neutral:
models receive the resulting snapshot, but they do not own source authority,
conflict resolution, or context-budget policy.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping, Protocol

from v2_brain_core import redact_sensitive


@dataclass(frozen=True)
class ContextSource:
    name: str
    authority: int
    payload: Mapping[str, Any]
    provenance: str = "runtime"
    required: bool = False
    observed_at: float = field(default_factory=time.time)


@dataclass(frozen=True)
class ContextConflict:
    key: str
    selected_source: str
    rejected_source: str
    selected_authority: int
    rejected_authority: int


@dataclass(frozen=True)
class ContextSnapshot:
    snapshot_id: str
    values: dict[str, Any]
    sources: tuple[dict[str, Any], ...]
    conflicts: tuple[ContextConflict, ...]
    dropped_keys: tuple[str, ...]
    budget_chars: int
    used_chars: int
    created_at: float = field(default_factory=time.time)


class MemoryRecallPort(Protocol):
    """Minimal long-term memory interface consumed by Context Engine."""

    def recall(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        ...


class NullMemoryRecall:
    def recall(self, query: str, *, limit: int = 8) -> list[dict[str, Any]]:
        del query, limit
        return []


class ContextEngine:
    def __init__(
        self,
        *,
        memory: MemoryRecallPort | None = None,
        default_budget_chars: int = 24000,
    ) -> None:
        if default_budget_chars < 1000:
            raise ValueError("context budget must be at least 1000 characters")
        self.memory = memory or NullMemoryRecall()
        self.default_budget_chars = default_budget_chars

    def build(
        self,
        sources: Iterable[ContextSource],
        *,
        objective: str | None = None,
        budget_chars: int | None = None,
    ) -> ContextSnapshot:
        budget = budget_chars or self.default_budget_chars
        if budget < 1000:
            raise ValueError("context budget must be at least 1000 characters")

        prepared = list(sources)
        if objective and objective.strip():
            recalled = self.memory.recall(objective.strip(), limit=8)
            if recalled:
                prepared.append(
                    ContextSource(
                        name="long_term_memory",
                        authority=55,
                        payload={"memory_recall": recalled},
                        provenance="memory",
                    )
                )

        # Higher authority wins. Stable source name ordering makes ties deterministic.
        ordered = sorted(prepared, key=lambda item: (-item.authority, item.name))
        selected: dict[str, tuple[ContextSource, Any]] = {}
        conflicts: list[ContextConflict] = []
        source_summaries: list[dict[str, Any]] = []

        for source in ordered:
            safe_payload = redact_sensitive(dict(source.payload))
            source_summaries.append(
                {
                    "name": source.name,
                    "authority": source.authority,
                    "provenance": source.provenance,
                    "required": source.required,
                    "observed_at": source.observed_at,
                    "keys": sorted(str(key) for key in safe_payload),
                }
            )
            for raw_key, value in safe_payload.items():
                key = str(raw_key)
                if key not in selected:
                    selected[key] = (source, value)
                    continue
                chosen_source, chosen_value = selected[key]
                if chosen_value == value:
                    continue
                conflicts.append(
                    ContextConflict(
                        key=key,
                        selected_source=chosen_source.name,
                        rejected_source=source.name,
                        selected_authority=chosen_source.authority,
                        rejected_authority=source.authority,
                    )
                )

        values: dict[str, Any] = {}
        dropped: list[str] = []
        used = 2

        # Required values first, then authority, then key for deterministic budgets.
        ranked = sorted(
            selected.items(),
            key=lambda item: (
                not item[1][0].required,
                -item[1][0].authority,
                item[0],
            ),
        )
        for key, (source, value) in ranked:
            encoded = json.dumps({key: value}, ensure_ascii=False, sort_keys=True)
            projected = used + len(encoded)
            if projected > budget and not source.required:
                dropped.append(key)
                continue
            values[key] = value
            used = projected

        return ContextSnapshot(
            snapshot_id=f"context-{int(time.time() * 1000)}",
            values=values,
            sources=tuple(source_summaries),
            conflicts=tuple(conflicts),
            dropped_keys=tuple(dropped),
            budget_chars=budget,
            used_chars=used,
        )

    @staticmethod
    def as_payload(snapshot: ContextSnapshot) -> dict[str, Any]:
        return {
            "snapshot_id": snapshot.snapshot_id,
            "values": snapshot.values,
            "sources": list(snapshot.sources),
            "conflicts": [asdict(item) for item in snapshot.conflicts],
            "dropped_keys": list(snapshot.dropped_keys),
            "budget_chars": snapshot.budget_chars,
            "used_chars": snapshot.used_chars,
            "created_at": snapshot.created_at,
        }
