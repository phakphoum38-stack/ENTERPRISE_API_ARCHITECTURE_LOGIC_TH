"""Deterministic AEOS failure algebra and novelty classification boundary.

This module does not decide truth. It canonicalizes a failure observation into a
stable fingerprint and classifies it against the explicit taxonomy. Unknown or
unclassified combinations remain non-passing states.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
from typing import Any, Mapping, Tuple

AXES = (
    "actor", "object", "boundary", "state", "time", "evidence",
    "authority", "dependency", "environment", "action", "consequence",
)
NON_PASS = frozenset({"NOT_OBSERVED", "UNKNOWN", "STALE", "CONFLICT", "UNCLASSIFIED"})


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _require_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


@dataclass(frozen=True)
class FailureObservation:
    actor: str
    object: str
    boundary: str
    state: str
    time: str
    evidence: str
    authority: str
    dependency: str
    environment: str
    action: str
    consequence: str
    evidence_refs: Tuple[str, ...] = ()
    source_sha: str = ""
    contract_version: str = ""
    policy_version: str = ""

    def __post_init__(self) -> None:
        for axis in AXES:
            _require_text(axis, getattr(self, axis))
        refs = tuple(self.evidence_refs)
        if len(set(refs)) != len(refs):
            raise ValueError("evidence_refs must be unique")
        for ref in refs:
            _require_text("evidence_ref", ref)
        for name in ("source_sha", "contract_version", "policy_version"):
            value = getattr(self, name)
            if value and not isinstance(value, str):
                raise ValueError(f"{name} must be a string")

    def canonical(self) -> Mapping[str, Any]:
        payload = asdict(self)
        payload["evidence_refs"] = list(self.evidence_refs)
        return payload

    @property
    def fingerprint(self) -> str:
        return digest(self.canonical())


def classify(observation: FailureObservation, known_classes: Mapping[str, Any]) -> str:
    """Return an explicit class, or UNCLASSIFIED when no rule matches.

    The function deliberately does not infer PASS from absence of a failure rule.
    """
    failure_taxonomy = known_classes.get("failure_taxonomy", {})
    tokens = " ".join(str(v).upper() for v in observation.canonical().values())
    matches = []
    for family, names in failure_taxonomy.items():
        for name in names if isinstance(names, list) else ():
            if str(name).upper() in tokens:
                matches.append(str(name))
    if len(set(matches)) == 1:
        return matches[0]
    return "UNCLASSIFIED"


def is_non_passing_state(state: str) -> bool:
    return _require_text("state", state).upper() in NON_PASS


def require_classified(observation: FailureObservation, known_classes: Mapping[str, Any]) -> str:
    classification = classify(observation, known_classes)
    if classification == "UNCLASSIFIED":
        raise ValueError("UNCLASSIFIED failure cannot pass the assurance boundary")
    return classification
