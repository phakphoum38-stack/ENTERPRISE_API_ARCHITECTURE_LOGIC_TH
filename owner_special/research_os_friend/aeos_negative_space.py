"""AEOS negative-space scanner.

Completion must prove absence of blockers, not merely presence of positive
signals. This boundary evaluates explicit inventory counts and forbidden
states, returning a deterministic report suitable for independent review.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class NegativeSpaceError(ValueError):
    """Raised when negative-space input is incomplete or malformed."""


_REQUIRED_ZERO_COUNTS = (
    "required_work",
    "recovery_work",
    "unresolved_failures",
    "unknown",
    "stale",
    "unverified",
    "blocked_required",
    "uncertified_integrations",
    "orphan_work",
    "unauthorized_mutations",
)


@dataclass(frozen=True)
class NegativeSpaceReport:
    passed: bool
    counts: Mapping[str, int]
    forbidden_states: tuple[str, ...]
    evidence_refs: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "PASS" if self.passed else "BLOCK",
            "counts": dict(self.counts),
            "forbidden_states": list(self.forbidden_states),
            "evidence_refs": list(self.evidence_refs),
        }


def scan_negative_space(
    *,
    counts: Mapping[str, int],
    forbidden_states: tuple[str, ...],
    evidence_refs: tuple[str, ...],
) -> NegativeSpaceReport:
    """Prove the absence of explicit completion blockers."""
    if not isinstance(counts, Mapping):
        raise NegativeSpaceError("counts required")
    normalized: dict[str, int] = {}
    for name in _REQUIRED_ZERO_COUNTS:
        value = counts.get(name)
        if type(value) is not int or value < 0:
            raise NegativeSpaceError(f"{name} must be a non-negative integer")
        normalized[name] = value
    if type(forbidden_states) is not tuple or any(not isinstance(state, str) or not state for state in forbidden_states):
        raise NegativeSpaceError("forbidden_states must be a tuple of names")
    if type(evidence_refs) is not tuple or not evidence_refs or any(not isinstance(ref, str) or not ref for ref in evidence_refs):
        raise NegativeSpaceError("negative-space evidence is required")
    if len(set(evidence_refs)) != len(evidence_refs):
        raise NegativeSpaceError("duplicate negative-space evidence reference")
    passed = all(value == 0 for value in normalized.values()) and not forbidden_states
    return NegativeSpaceReport(
        passed=passed,
        counts=normalized,
        forbidden_states=forbidden_states,
        evidence_refs=evidence_refs,
    )
