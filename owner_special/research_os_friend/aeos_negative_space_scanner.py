"""Concrete AEOS negative-space inventory adapter.

The existing negative-space gate evaluates counts, but counts must come from an
observed inventory rather than being declared directly by the completion
caller. This adapter normalizes an externally collected inventory into the
strict count contract and emits evidence references for independent review.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .aeos_negative_space import NegativeSpaceReport, scan_negative_space


class NegativeSpaceScannerError(ValueError):
    """Raised when the observed inventory cannot be normalized safely."""


_ZERO_KINDS = (
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
class InventoryItem:
    item_id: str
    kind: str
    state: str
    required: bool = False


def scan_observed_inventory(
    *,
    items: Iterable[InventoryItem],
    evidence_refs: tuple[str, ...],
) -> NegativeSpaceReport:
    """Derive negative-space counts from observed inventory records.

    The adapter intentionally has no completion opinion beyond the normalized
    inventory. Unknown kinds are rejected instead of silently disappearing.
    """
    if type(evidence_refs) is not tuple or not evidence_refs or len(set(evidence_refs)) != len(evidence_refs):
        raise NegativeSpaceScannerError("unique evidence references required")
    normalized = tuple(items)
    if any(not isinstance(item, InventoryItem) for item in normalized):
        raise NegativeSpaceScannerError("inventory must contain InventoryItem records")

    counts = {kind: 0 for kind in _ZERO_KINDS}
    forbidden_states: list[str] = []
    for item in normalized:
        if not item.item_id or not item.kind or not item.state:
            raise NegativeSpaceScannerError("inventory item identity and state are required")
        if item.kind not in _ZERO_KINDS:
            raise NegativeSpaceScannerError(f"unknown inventory kind: {item.kind}")
        if type(item.required) is not bool:
            raise NegativeSpaceScannerError("inventory required flag must be boolean")
        counts[item.kind] += 1
        if item.state in {"UNKNOWN", "STALE", "UNVERIFIED", "BLOCKED", "QUARANTINED", "REVOKED", "EXPIRED", "CONFLICT"}:
            forbidden_states.append(f"{item.kind}:{item.item_id}:{item.state}")

    return scan_negative_space(
        counts=counts,
        forbidden_states=tuple(sorted(forbidden_states)),
        evidence_refs=evidence_refs,
    )
