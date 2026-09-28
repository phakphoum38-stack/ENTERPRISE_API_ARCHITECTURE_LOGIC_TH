"""Fail-closed main-baseline re-anchor boundary for AEOS.

This module does not read Git or perform mutations. A trusted repository adapter
must supply the observed main SHA and evidence. The boundary only permits a
re-anchor when the observation is structurally valid and the previous evidence
was bound to the exact baseline that was observed.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Tuple


class ReanchorError(ValueError):
    """Raised when a main-baseline re-anchor invariant is violated."""


def _sha(value: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise ReanchorError("commit SHA must be a 40-character lowercase hexadecimal value")
    return value


@dataclass(frozen=True)
class ReanchorObservation:
    mission_id: str
    previous_baseline_sha: str
    observed_main_sha: str
    evidence_refs: Tuple[str, ...]
    evidence_digest: str
    main_verified: bool = True

    def __post_init__(self) -> None:
        if not self.mission_id:
            raise ReanchorError("mission_id is required")
        _sha(self.previous_baseline_sha)
        _sha(self.observed_main_sha)
        if not self.evidence_refs or any(not isinstance(ref, str) or not ref for ref in self.evidence_refs):
            raise ReanchorError("non-empty evidence_refs are required")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ReanchorError("duplicate evidence reference")
        if type(self.main_verified) is not bool or not self.main_verified:
            raise ReanchorError("main must be independently verified before re-anchor")
        expected = _digest(self.mission_id, self.previous_baseline_sha, self.observed_main_sha, self.evidence_refs)
        if self.evidence_digest != expected:
            raise ReanchorError("evidence digest mismatch")


def _digest(mission_id: str, previous_baseline_sha: str, observed_main_sha: str, evidence_refs: Tuple[str, ...]) -> str:
    payload = {
        "mission_id": mission_id,
        "previous_baseline_sha": previous_baseline_sha,
        "observed_main_sha": observed_main_sha,
        "evidence_refs": list(evidence_refs),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def create_reanchor_observation(
    *,
    mission_id: str,
    previous_baseline_sha: str,
    observed_main_sha: str,
    evidence_refs: Tuple[str, ...],
    main_verified: bool = True,
) -> ReanchorObservation:
    """Create a deterministic observation; no repository state is inferred."""
    _sha(previous_baseline_sha)
    _sha(observed_main_sha)
    if type(main_verified) is not bool or not main_verified:
        raise ReanchorError("main must be independently verified")
    refs = tuple(evidence_refs)
    digest = _digest(mission_id, previous_baseline_sha, observed_main_sha, refs)
    return ReanchorObservation(
        mission_id=mission_id,
        previous_baseline_sha=previous_baseline_sha,
        observed_main_sha=observed_main_sha,
        evidence_refs=refs,
        evidence_digest=digest,
        main_verified=main_verified,
    )


def reanchor_baseline(observation: ReanchorObservation) -> str:
    """Return the only baseline that may follow an independently verified observation."""
    if not isinstance(observation, ReanchorObservation):
        raise TypeError("re-anchor requires a verified ReanchorObservation")
    return observation.observed_main_sha
