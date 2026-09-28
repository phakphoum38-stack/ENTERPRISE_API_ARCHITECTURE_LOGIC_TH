"""Fail-closed novelty firewall for AEOS assurance decisions."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple

KNOWN = frozenset({"KNOWN", "VALID", "VERIFIED", "CERTIFIED"})
BLOCKED = frozenset({"NOT_OBSERVED", "UNKNOWN", "STALE", "CONFLICT", "UNCLASSIFIED", "NOVEL"})


@dataclass(frozen=True)
class NoveltyDecision:
    classification: str
    allowed_to_certify: bool
    reason: str
    required_actions: Tuple[str, ...]


def evaluate_novelty(classification: str, *, independently_verified: bool = False) -> NoveltyDecision:
    """Gate novelty without treating absence of a known failure as success."""
    value = classification.strip().upper()
    if not value:
        raise ValueError("classification must be non-empty")
    if value in BLOCKED:
        return NoveltyDecision(
            value,
            False,
            "novel-or-nonpassing state requires fail-closed handling",
            ("PRESERVE", "CLASSIFY", "ROOT_CAUSE", "CONTRACT_OR_TEST", "REVERIFY"),
        )
    if value == "VERIFIED" and not independently_verified:
        return NoveltyDecision(
            value,
            False,
            "verification claim lacks independent-verifier proof",
            ("INDEPENDENT_VERIFY",),
        )
    if value == "CERTIFIED":
        return NoveltyDecision(value, True, "already certified by an upstream governed boundary", ())
    if value in KNOWN:
        return NoveltyDecision(value, False, "known state still requires the appropriate certification boundary", ("CERTIFY",))
    return NoveltyDecision(
        "UNCLASSIFIED",
        False,
        "unknown classification is not evidence of safety",
        ("PRESERVE", "CLASSIFY", "ROOT_CAUSE", "CONTRACT_OR_TEST", "REVERIFY"),
    )


def require_certifiable(classification: str, *, independently_verified: bool = False) -> None:
    decision = evaluate_novelty(classification, independently_verified=independently_verified)
    if not decision.allowed_to_certify:
        raise ValueError(f"assurance blocked: {decision.reason}")
