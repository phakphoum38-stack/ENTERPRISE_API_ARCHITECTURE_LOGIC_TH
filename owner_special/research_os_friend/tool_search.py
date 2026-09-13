from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .unified_tool_catalog import ToolDescriptor, ToolState, UnifiedToolCatalog


@dataclass(frozen=True)
class ToolSearchResult:
    name: str
    capability: str
    source: str
    state: str
    optional: bool
    dependency: str | None
    score: int


class ToolSearch:
    """Deterministic, read-only discovery over the unified tool catalog.

    Search never executes a tool and never changes tool registration or policy.
    """

    def __init__(self, catalog: UnifiedToolCatalog | None = None) -> None:
        self._catalog = catalog or UnifiedToolCatalog()

    @staticmethod
    def _tokens(text: str) -> tuple[str, ...]:
        return tuple(token for token in re.split(r"[^a-z0-9_.-]+", text.lower()) if token)

    @classmethod
    def _score(cls, query: str, descriptor: ToolDescriptor) -> int:
        query_text = query.strip().lower()
        tokens = cls._tokens(query_text)
        haystack = " ".join(
            item
            for item in (
                descriptor.name,
                descriptor.capability,
                descriptor.source,
                descriptor.state.value,
                descriptor.dependency or "",
            )
            if item
        ).lower()
        score = 0
        if not query_text:
            return 0
        if query_text == descriptor.name.lower():
            score += 100
        if query_text == descriptor.capability.lower():
            score += 90
        if query_text in descriptor.name.lower():
            score += 40
        if query_text in descriptor.capability.lower():
            score += 30
        if query_text in haystack:
            score += 10
        score += sum(5 for token in tokens if token in haystack)
        return score

    def search(
        self,
        query: str,
        *,
        states: Iterable[ToolState] | None = None,
        sources: Iterable[str] | None = None,
        limit: int = 8,
    ) -> tuple[ToolSearchResult, ...]:
        if limit < 1:
            raise ValueError("limit must be >= 1")
        allowed_states = set(states) if states is not None else None
        allowed_sources = set(sources) if sources is not None else None
        candidates: list[ToolSearchResult] = []
        for descriptor in self._catalog.all():
            if allowed_states is not None and descriptor.state not in allowed_states:
                continue
            if allowed_sources is not None and descriptor.source not in allowed_sources:
                continue
            score = self._score(query, descriptor)
            if query.strip() and score == 0:
                continue
            candidates.append(
                ToolSearchResult(
                    name=descriptor.name,
                    capability=descriptor.capability,
                    source=descriptor.source,
                    state=descriptor.state.value,
                    optional=descriptor.optional,
                    dependency=descriptor.dependency,
                    score=score,
                )
            )
        candidates.sort(key=lambda item: (-item.score, item.name))
        return tuple(candidates[:limit])
