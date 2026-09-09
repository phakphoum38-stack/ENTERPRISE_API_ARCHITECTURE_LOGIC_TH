"""Deterministic semantic-change classification for AEOS.

The classifier describes an input pair; it does not certify repository reality.
Nested changes are represented as canonical semantic paths and both inputs are
fingerprinted so the returned proof can be replayed independently.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
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
    before_digest: str
    after_digest: str
    change_proof: tuple[tuple[str, str, str], ...]


def _canonical(value: Any) -> str:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    except (TypeError, ValueError) as exc:
        raise SemanticDiffError("inputs must be JSON-canonicalizable") from exc


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _validate_path_segment(segment: Any) -> str:
    if not isinstance(segment, str) or not segment:
        raise SemanticDiffError("mapping keys must be non-empty strings")
    return segment


def _flatten(value: Any, path: str = "$") -> dict[str, Any]:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key in sorted(value):
            segment = _validate_path_segment(key)
            result.update(_flatten(value[key], f"{path}.{segment}"))
        if not value:
            result[path] = {}
        return result
    if isinstance(value, list):
        result = {}
        if not value:
            result[path] = []
        for index, item in enumerate(value):
            result.update(_flatten(item, f"{path}[{index}]"))
        return result
    return {path: value}


def classify_semantic_diff(
    *,
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    breaking_fields: tuple[str, ...] = (
        "authority", "scope", "contract", "policy", "schema", "api", "capability"
    ),
) -> SemanticDiff:
    if not isinstance(before, Mapping) or not isinstance(after, Mapping):
        raise SemanticDiffError("mapping inputs required")
    if not isinstance(breaking_fields, tuple):
        raise SemanticDiffError("breaking_fields must be a tuple")
    if any(not isinstance(field, str) or not field for field in breaking_fields):
        raise SemanticDiffError("breaking_fields must contain non-empty strings")
    if len(set(breaking_fields)) != len(breaking_fields):
        raise SemanticDiffError("breaking_fields must be unique")

    before_flat = _flatten(before)
    after_flat = _flatten(after)
    paths = tuple(sorted(set(before_flat) | set(after_flat)))
    changed = tuple(path for path in paths if before_flat.get(path) != after_flat.get(path))
    change_proof = tuple(
        (path, _digest(before_flat[path]) if path in before_flat else "MISSING", _digest(after_flat[path]) if path in after_flat else "MISSING")
        for path in changed
    )

    def touches(field: str) -> bool:
        prefix = f"$.{field}"
        return any(path == prefix or path.startswith(prefix + ".") or path.startswith(prefix + "[") for path in changed)

    breaking = any(touches(field) for field in breaking_fields)
    contract_changed = touches("contract")
    policy_changed = touches("policy")
    authority_changed = touches("authority")
    risk = "CRITICAL" if authority_changed else "HIGH" if breaking else "LOW" if not changed else "MEDIUM"
    before_digest = _digest(before)
    after_digest = _digest(after)
    payload = {
        "before_digest": before_digest,
        "after_digest": after_digest,
        "changed": list(changed),
        "change_proof": [list(item) for item in change_proof],
        "breaking": breaking,
        "contract_changed": contract_changed,
        "policy_changed": policy_changed,
        "risk": risk,
    }
    return SemanticDiff(
        changed, breaking, contract_changed, policy_changed, risk,
        _digest(payload), before_digest, after_digest, change_proof,
    )
