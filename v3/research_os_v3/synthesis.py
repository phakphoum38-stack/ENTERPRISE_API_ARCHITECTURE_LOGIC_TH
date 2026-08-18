from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .evidence import Evidence


@dataclass(frozen=True)
class Finding:
    claim: str
    evidence_ids: tuple[str, ...]
    confidence: float
    sources: tuple[str, ...]


@dataclass(frozen=True)
class SynthesisResult:
    question: str
    findings: tuple[Finding, ...]
    conflicts: tuple[tuple[str, str], ...]
    conclusion: str


class ResearchSynthesizer:
    """Deterministic synthesis boundary.

    It does not invent facts. Every finding must originate from supplied
    evidence, while conflict detection exposes incompatible claims for a
    higher-level reasoning model or human reviewer.
    """

    def synthesize(self, question: str, evidence: Iterable[Evidence]) -> SynthesisResult:
        items = tuple(evidence)
        groups: dict[str, list[Evidence]] = {}
        for item in items:
            groups.setdefault(item.claim.strip().casefold(), []).append(item)

        findings: list[Finding] = []
        for group in groups.values():
            confidence = max(item.confidence for item in group)
            findings.append(
                Finding(
                    claim=group[0].claim,
                    evidence_ids=tuple(item.id for item in group),
                    confidence=confidence,
                    sources=tuple(dict.fromkeys(item.source_uri for item in group)),
                )
            )

        conflicts = self._detect_conflicts(findings)
        if not findings:
            conclusion = "Insufficient evidence to reach a conclusion."
        elif conflicts:
            conclusion = (
                f"Research produced {len(findings)} supported finding(s) with "
                f"{len(conflicts)} potential conflict(s) requiring review."
            )
        else:
            conclusion = f"Research produced {len(findings)} supported finding(s)."

        return SynthesisResult(
            question=question,
            findings=tuple(findings),
            conflicts=conflicts,
            conclusion=conclusion,
        )

    @staticmethod
    def _detect_conflicts(findings: list[Finding]) -> tuple[tuple[str, str], ...]:
        conflicts: list[tuple[str, str]] = []
        # Deliberately conservative: only explicit negation is treated as a
        # potential contradiction. Semantic contradiction belongs to the LLM
        # reasoning layer, not this deterministic domain boundary.
        for index, left in enumerate(findings):
            for right in findings[index + 1 :]:
                a = left.claim.casefold().strip()
                b = right.claim.casefold().strip()
                if a == f"not {b}" or b == f"not {a}":
                    conflicts.append((left.claim, right.claim))
        return tuple(conflicts)
