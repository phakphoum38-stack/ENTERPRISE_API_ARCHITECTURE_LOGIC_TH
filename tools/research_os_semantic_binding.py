#!/usr/bin/env python3
"""Canonical semantic binding resolver for Research OS assurance artifacts.

The resolver is deliberately descriptive and fail-closed. It does not grant
authorization or release authority; FINAL_GATE remains the sole release
authority. M.2 uses this module for semantic identity fallback so that the
audit graph does not maintain a second resolution algorithm.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


SEMANTIC_ASSURANCE_RELATIONS = frozenset(
    {"VERIFIED_BY", "ENFORCED_BY", "DISPATCHED_BY", "SUPPORTED_BY", "BOUND_TO"}
)
SINGLE_CARDINALITY_RELATIONS = frozenset(
    {"BOUND_TO", "ENFORCED_BY", "DISPATCHED_BY"}
)


@dataclass(frozen=True)
class BindingResult:
    relation: str
    targets: tuple[str, ...]
    tier: str | None
    ambiguous: bool
    unresolved: bool
    candidates: tuple[str, ...]


def contract_stem(path: str) -> str:
    stem = Path(path).stem.lower()
    for suffix in ("_contract", "-contract"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break
    return stem


def declared_identities(path: str, text: str) -> set[str]:
    """Extract conservative canonical identities from artifact metadata."""
    values = {contract_stem(path)}
    for pattern in (
        r'"(?:contract|contract_id|capability_id|component_id)"\s*:\s*"([A-Za-z0-9_.:/-]+)"',
        r'^(?:contract|contract_id|capability_id|component_id):\s*([A-Za-z0-9_.:/-]+)',
    ):
        values.update(x.lower() for x in re.findall(pattern, text, re.MULTILINE))
    return {x for x in values if x}


def resolve_semantic_binding(
    *,
    target: str,
    relation: str,
    candidates: list[str],
    texts: dict[str, str],
) -> BindingResult:
    """Resolve one semantic relation using unique canonical identity overlap.

    This is intentionally limited to semantic fallback. Explicit path,
    explicit contract-reference, and structured graph edges remain the
    responsibility of the caller. Multiple identity matches are ambiguous
    rather than auto-selected.
    """
    if relation not in SEMANTIC_ASSURANCE_RELATIONS:
        raise ValueError(f"unsupported semantic assurance relation: {relation}")

    identities = declared_identities(target, texts.get(target, ""))
    matches = tuple(
        sorted(
            path
            for path in candidates
            if identities
            & declared_identities(path, texts.get(path, ""))
        )
    )

    if len(matches) == 1:
        return BindingResult(
            relation=relation,
            targets=matches,
            tier="unique_semantic_identity",
            ambiguous=False,
            unresolved=False,
            candidates=matches,
        )

    if len(matches) > 1 and relation in SINGLE_CARDINALITY_RELATIONS:
        return BindingResult(
            relation=relation,
            targets=(),
            tier=None,
            ambiguous=True,
            unresolved=False,
            candidates=matches,
        )

    return BindingResult(
        relation=relation,
        targets=(),
        tier=None,
        ambiguous=False,
        unresolved=True,
        candidates=matches,
    )
