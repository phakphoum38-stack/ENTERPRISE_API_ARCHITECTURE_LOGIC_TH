"""AEOS anti-circularity and evidence-independence boundary.

Multiple records from the same source do not become independent evidence.
The verifier must be distinct from the implementation under verification, and
certificate evidence must not secretly depend on the subject being certified.
"""
from __future__ import annotations

from dataclasses import dataclass


class CircularityError(ValueError):
    """Raised when an assurance graph contains an invalid trust cycle."""


@dataclass(frozen=True)
class IndependenceDecision:
    independent: bool
    reason: str
    common_sources: tuple[str, ...]


def evaluate_independence(
    *,
    subject_id: str,
    verifier_id: str,
    subject_sources: tuple[str, ...],
    verifier_sources: tuple[str, ...],
    evidence_sources: tuple[str, ...],
) -> IndependenceDecision:
    """Reject self-verification and undisclosed common-source evidence."""
    values = (subject_id, verifier_id)
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise CircularityError("subject and verifier identities are required")
    if subject_id == verifier_id:
        return IndependenceDecision(False, "verifier identity equals subject identity", ())
    for name, sources in (("subject", subject_sources), ("verifier", verifier_sources), ("evidence", evidence_sources)):
        if type(sources) is not tuple or not sources or any(not isinstance(source, str) or not source.strip() for source in sources):
            raise CircularityError(f"{name} sources are required")
        if len(set(sources)) != len(sources):
            raise CircularityError(f"duplicate {name} source")

    common = tuple(sorted(set(subject_sources).intersection(verifier_sources)))
    if common:
        return IndependenceDecision(False, "subject and verifier share a common source", common)
    evidence_common = tuple(sorted(set(evidence_sources).intersection(subject_sources)))
    if evidence_common:
        return IndependenceDecision(False, "evidence source is also the subject source", evidence_common)
    return IndependenceDecision(True, "verifier and evidence sources are independent of subject sources", ())
