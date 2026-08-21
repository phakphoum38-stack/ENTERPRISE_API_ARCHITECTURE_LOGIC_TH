from __future__ import annotations

from urllib.parse import urlparse

from .models import Evidence


class ResearchIndex:
    """Evidence-first research index; network retrieval is intentionally injected."""

    def __init__(self) -> None:
        self._evidence: list[Evidence] = []

    def add(self, evidence: Evidence) -> None:
        if evidence.confidence < 0 or evidence.confidence > 1:
            raise ValueError("confidence must be between 0 and 1")
        if evidence.url:
            parsed = urlparse(evidence.url)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError("evidence URL must be a valid HTTP(S) URL")
        self._evidence.append(evidence)

    def trusted(self, minimum_confidence: float = 0.75) -> tuple[Evidence, ...]:
        if not 0 <= minimum_confidence <= 1:
            raise ValueError("minimum_confidence must be between 0 and 1")
        return tuple(sorted(
            (e for e in self._evidence if e.confidence >= minimum_confidence),
            key=lambda item: item.confidence,
            reverse=True,
        ))

    def all(self) -> tuple[Evidence, ...]:
        return tuple(self._evidence)

    def require_consensus(self, minimum_confidence: float = 0.75, minimum_sources: int = 2) -> tuple[Evidence, ...]:
        trusted = self.trusted(minimum_confidence)
        if len(trusted) < minimum_sources:
            raise LookupError("insufficient independent evidence")
        return trusted
