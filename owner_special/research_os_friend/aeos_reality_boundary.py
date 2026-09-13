"""AEOS reality-observation trust boundary.

Reality adapters may observe external state, but an observation is never a
certificate. The boundary binds observations to exact identity, contract,
policy, time, and evidence references without pretending to perform the
underlying repository/CI/runtime scan itself.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


class RealityObservationError(ValueError):
    """Raised when a reality observation cannot be safely bound."""


_GIT_SHA = 40
_SHA256 = 64


def _sha(value: str, length: int) -> None:
    if not isinstance(value, str) or len(value) != length:
        raise RealityObservationError("invalid SHA binding")
    if any(char not in "0123456789abcdef" for char in value):
        raise RealityObservationError("invalid SHA binding")


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RealityObservation:
    observation_id: str
    subject: str
    baseline_sha: str
    observed_sha: str
    contract_sha256: str
    policy_sha256: str
    observed_at: str
    source: str
    status: str
    facts: Mapping[str, Any]
    evidence_refs: tuple[str, ...]
    evidence_digest: str
    verifier_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.observation_id, str) or not self.observation_id:
            raise RealityObservationError("observation_id required")
        if not isinstance(self.subject, str) or not self.subject:
            raise RealityObservationError("subject required")
        for value in (self.baseline_sha, self.observed_sha):
            _sha(value, _GIT_SHA)
        for value in (self.contract_sha256, self.policy_sha256, self.evidence_digest):
            _sha(value, _SHA256)
        if self.observed_sha != self.baseline_sha:
            raise RealityObservationError("observation is stale")
        if not isinstance(self.observed_at, str) or not self.observed_at:
            raise RealityObservationError("observed_at required")
        if not isinstance(self.source, str) or not self.source:
            raise RealityObservationError("source required")
        if self.status not in {"VALID", "INVALID", "UNKNOWN", "CONFLICT", "STALE", "QUARANTINED"}:
            raise RealityObservationError("invalid observation status")
        if not isinstance(self.facts, Mapping) or not self.facts:
            raise RealityObservationError("facts required")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise RealityObservationError("evidence_refs required")
        if any(not isinstance(ref, str) or not ref for ref in self.evidence_refs):
            raise RealityObservationError("invalid evidence reference")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise RealityObservationError("duplicate evidence reference")
        if self.verifier_id is not None and (not isinstance(self.verifier_id, str) or not self.verifier_id):
            raise RealityObservationError("invalid verifier_id")


def bind_reality_observation(
    *,
    observation_id: str,
    subject: str,
    baseline_sha: str,
    observed_sha: str,
    contract_sha256: str,
    policy_sha256: str,
    observed_at: str,
    source: str,
    status: str,
    facts: Mapping[str, Any],
    evidence_refs: tuple[str, ...],
    verifier_id: str | None = None,
) -> RealityObservation:
    """Create a deterministic observation envelope from adapter facts.

    The adapter remains responsible for obtaining the facts. This function
    only validates and binds them; it does not elevate status to VERIFIED.
    """
    _sha(baseline_sha, _GIT_SHA)
    _sha(observed_sha, _GIT_SHA)
    for value in (contract_sha256, policy_sha256):
        _sha(value, _SHA256)
    if observed_sha != baseline_sha:
        raise RealityObservationError("observed SHA differs from baseline")
    if not isinstance(facts, Mapping) or not facts:
        raise RealityObservationError("facts required")
    refs = tuple(evidence_refs)
    if not refs or len(set(refs)) != len(refs) or any(not isinstance(ref, str) or not ref for ref in refs):
        raise RealityObservationError("invalid evidence references")
    evidence_digest = _digest(
        {
            "baseline_sha": baseline_sha,
            "contract_sha256": contract_sha256,
            "policy_sha256": policy_sha256,
            "observed_at": observed_at,
            "source": source,
            "status": status,
            "facts": facts,
            "evidence_refs": refs,
        }
    )
    return RealityObservation(
        observation_id=observation_id,
        subject=subject,
        baseline_sha=baseline_sha,
        observed_sha=observed_sha,
        contract_sha256=contract_sha256,
        policy_sha256=policy_sha256,
        observed_at=observed_at,
        source=source,
        status=status,
        facts=dict(facts),
        evidence_refs=refs,
        evidence_digest=evidence_digest,
        verifier_id=verifier_id,
    )
