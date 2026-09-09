"""AEOS observation-to-mutation TOCTOU boundary.

An observation is only usable for mutation when its exact baseline, lease,
and evidence digest are rebound immediately before the mutation. This module
is deliberately side-effect-free; the trusted executor performs the actual
mutation after this boundary succeeds.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


class TOCTOUError(ValueError):
    """Raised when an observation cannot be safely rebound to a mutation."""


def _sha(value: str, *, name: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise TOCTOUError(f"invalid {name}")
    return value


def _refs(value: tuple[str, ...], *, name: str = "evidence_refs") -> tuple[str, ...]:
    if not isinstance(value, tuple) or not value or any(not isinstance(item, str) or not item for item in value):
        raise TOCTOUError(f"invalid {name}")
    if len(set(value)) != len(value):
        raise TOCTOUError(f"duplicate {name}")
    return value


def _digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class MutationBinding:
    work_id: str
    baseline_sha: str
    observed_sha: str
    lease_id: str
    evidence_refs: tuple[str, ...]
    evidence_digest: str
    rebound: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.work_id, str) or not self.work_id:
            raise TOCTOUError("invalid work_id")
        _sha(self.baseline_sha, name="baseline_sha")
        _sha(self.observed_sha, name="observed_sha")
        if self.observed_sha != self.baseline_sha:
            raise TOCTOUError("observed SHA differs from baseline")
        if not isinstance(self.lease_id, str) or not self.lease_id:
            raise TOCTOUError("invalid lease_id")
        _refs(self.evidence_refs)
        if not isinstance(self.evidence_digest, str) or len(self.evidence_digest) != 64:
            raise TOCTOUError("invalid evidence_digest")
        if type(self.rebound) is not bool or not self.rebound:
            raise TOCTOUError("mutation binding must be rebound")


def bind_observation_for_mutation(
    *,
    work_id: str,
    baseline_sha: str,
    observed_sha: str,
    lease_id: str,
    evidence_refs: tuple[str, ...],
    evidence_digest: str,
    current_sha: str,
    current_lease_id: str,
) -> MutationBinding:
    """Rebind an independently observed state immediately before mutation."""
    binding = MutationBinding(
        work_id=work_id,
        baseline_sha=_sha(baseline_sha, name="baseline_sha"),
        observed_sha=_sha(observed_sha, name="observed_sha"),
        lease_id=lease_id,
        evidence_refs=evidence_refs,
        evidence_digest=evidence_digest,
    )
    _sha(current_sha, name="current_sha")
    if current_sha != binding.baseline_sha:
        raise TOCTOUError("current SHA changed since observation")
    if current_lease_id != binding.lease_id:
        raise TOCTOUError("lease changed since observation")
    expected = _digest({"work_id": work_id, "baseline_sha": baseline_sha, "observed_sha": observed_sha, "lease_id": lease_id, "evidence_refs": list(evidence_refs)})
    if evidence_digest != expected:
        raise TOCTOUError("evidence digest mismatch")
    return binding
