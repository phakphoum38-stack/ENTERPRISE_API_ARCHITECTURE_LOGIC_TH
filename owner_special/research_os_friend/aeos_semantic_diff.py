"""Deterministic semantic-change classification for AEOS."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


class SemanticDiffError(ValueError):
    """Raised for malformed or unsafe semantic diff input."""


@dataclass(frozen=True)
class SemanticDiff:
    changed: tuple[str, ...]
    breaking: bool
    contract_changed: bool
    policy_changed: bool
    risk: str
    digest: str


def _digest(value: Any) -> str:
    import hashlib, json
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def classify_semantic_diff(*, before: Mapping[str, Any], after: Mapping[str, Any], breaking_fields: tuple[str, ...] = ("authority", "scope", "contract", "policy", "schema", "api", "capability")) -> SemanticDiff:
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise SemanticDiffError("mapping inputs required")
    if not isinstance(breaking_fields, tuple) or len(set(breaking_fields)) != len(breaking_fields):
        raise SemanticDiffError("breaking_fields must be a unique tuple")
    changed = tuple(sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key)))
    breaking = any(key in breaking_fields for key in changed)
    contract_changed = "contract" in changed
    policy_changed = "policy" in changed
    risk = "CRITICAL" if "authority" in changed else "HIGH" if breaking else "LOW" if not changed else "MEDIUM"
    payload = {"changed": list(changed), "breaking": breaking, "contract_changed": contract_changed, "policy_changed": policy_changed, "risk": risk}
    return SemanticDiff(changed, breaking, contract_changed, policy_changed, risk, _digest(payload))
