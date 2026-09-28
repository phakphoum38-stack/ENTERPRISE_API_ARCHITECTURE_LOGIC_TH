"""Fail-closed recovery primitives for AEOS work items.

Recovery records are immutable descriptions of a verified checkpoint. Actual
storage and rollback adapters are deliberately external to this module.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


class RecoveryError(ValueError):
    """Raised when a recovery invariant is violated."""


def _sha(value: str) -> str:
    if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise RecoveryError("checkpoint SHA must be a 40-character lowercase commit SHA")
    return value


def _digest(value: Mapping[str, Any]) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class RecoveryCheckpoint:
    checkpoint_id: str
    mission_id: str
    work_id: str
    baseline_sha: str
    state_digest: str
    evidence_refs: tuple[str, ...]
    reversible: bool = True

    def __post_init__(self) -> None:
        if not self.checkpoint_id or not self.mission_id or not self.work_id:
            raise RecoveryError("checkpoint identity fields are required")
        _sha(self.baseline_sha)
        if not isinstance(self.state_digest, str) or len(self.state_digest) != 64:
            raise RecoveryError("state_digest must be SHA-256")
        if not self.evidence_refs or any(not isinstance(x, str) or not x for x in self.evidence_refs):
            raise RecoveryError("checkpoint requires evidence references")
        if type(self.reversible) is not bool:
            raise RecoveryError("reversible must be a strict boolean")


def create_checkpoint(
    *, checkpoint_id: str, mission_id: str, work_id: str,
    baseline_sha: str, state: Mapping[str, Any], evidence_refs: tuple[str, ...],
    reversible: bool = True,
) -> RecoveryCheckpoint:
    """Create a deterministic checkpoint from explicit state and evidence."""
    if not isinstance(state, Mapping):
        raise RecoveryError("state must be a mapping")
    return RecoveryCheckpoint(
        checkpoint_id=checkpoint_id,
        mission_id=mission_id,
        work_id=work_id,
        baseline_sha=_sha(baseline_sha),
        state_digest=_digest(state),
        evidence_refs=tuple(evidence_refs),
        reversible=reversible,
    )


def validate_rollback_request(
    checkpoint: RecoveryCheckpoint,
    *, observed_sha: str,
    requested_work_id: str,
    evidence_refs: tuple[str, ...],
) -> None:
    """Validate a rollback request without performing the rollback."""
    if not isinstance(checkpoint, RecoveryCheckpoint):
        raise RecoveryError("rollback requires a recovery checkpoint")
    if not checkpoint.reversible:
        raise RecoveryError("checkpoint is not reversible")
    if requested_work_id != checkpoint.work_id:
        raise RecoveryError("rollback work identity mismatch")
    if observed_sha != checkpoint.baseline_sha:
        raise RecoveryError("rollback observed SHA does not match checkpoint baseline")
    if not evidence_refs or tuple(evidence_refs) != checkpoint.evidence_refs:
        raise RecoveryError("rollback evidence does not exactly match checkpoint evidence")
