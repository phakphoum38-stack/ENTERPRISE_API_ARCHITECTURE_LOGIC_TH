"""Independent verification boundary for AEOS completion observations.

The workloop is intentionally a pure state machine. This module is the
separate trust boundary that accepts observations only when they carry an
exact baseline, a complete ordered scan, and a deterministic evidence digest.
It does not discover repository state itself; concrete scanners supply the
observations and their evidence. That keeps discovery separate from the
stop-proof projection and prevents a caller from promoting unverified values
directly to CERTIFIED_IDLE.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Mapping


class CompletionVerificationError(ValueError):
    """Raised when completion observations cannot be independently verified."""


_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_COUNTS = (
    "required_work",
    "recovery_work",
    "unresolved_failures",
    "unknown",
    "stale",
    "unverified",
    "blocked_required",
    "uncertified_integrations",
)
_REQUIRED_BOOLS = ("main_verified", "final_rescan")
_REQUIRED_SCANS = (
    "mission_scan",
    "dependency_scan",
    "queue_scan",
    "recovery_scan",
    "pull_request_scan",
    "branch_scan",
    "ci_scan",
    "failure_scan",
    "unknown_scan",
    "stale_scan",
    "evidence_scan",
    "provenance_scan",
    "governance_scan",
    "main_scan",
    "final_rescan",
)

# Construction is intentionally sealed. A caller must go through
# verify_completion_observation(), which is the only code path that mints
# this token. The stop controller checks the private seal rather than a
# caller-controlled ``verified=True`` field or an exposed factory method.
_VERIFICATION_SEAL = object()


@dataclass(frozen=True, init=False)
class VerifiedCompletionObservation:
    baseline_sha: str
    scan_order: tuple[str, ...]
    observations: Mapping[str, Any]
    evidence_digest: str
    _verification_seal: object = field(repr=False, compare=False)

    @property
    def verified(self) -> bool:
        """Compatibility view; truth comes only from the private verifier seal."""
        return self.is_verifier_issued()

    def is_verifier_issued(self) -> bool:
        """Return true only for an object minted by this verification boundary."""
        return getattr(self, "_verification_seal", None) is _VERIFICATION_SEAL

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "research-os-aeos-completion-observation/v1",
            "verified": self.verified,
            "baseline_sha": self.baseline_sha,
            "scan_order": list(self.scan_order),
            "observations": dict(self.observations),
            "evidence_digest": self.evidence_digest,
        }


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    material = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return hashlib.sha256(material).hexdigest()


def verify_completion_observation(
    *,
    baseline_sha: str,
    observed_sha: str,
    scan_results: Mapping[str, Any],
    evidence_refs: tuple[str, ...],
) -> VerifiedCompletionObservation:
    """Verify a scanner result before it can feed the AEOS stop-proof.

    The function requires the complete contract-defined scan order, an exact
    baseline match, strict scalar types, and at least one evidence reference.
    Every scan must explicitly report PASS. No missing or UNKNOWN value is
    coerced into a passing value.
    """
    if not _SHA_RE.fullmatch(baseline_sha) or not _SHA_RE.fullmatch(observed_sha):
        raise CompletionVerificationError("baseline and observed SHA must be 40-character lowercase commit SHAs")
    if observed_sha != baseline_sha:
        raise CompletionVerificationError("completion observation is stale: observed SHA does not match baseline")
    if type(evidence_refs) is not tuple or not evidence_refs or any(not isinstance(ref, str) or not ref.strip() for ref in evidence_refs):
        raise CompletionVerificationError("completion verification requires non-empty evidence references")

    supplied_order = scan_results.get("scan_order")
    if type(supplied_order) is not tuple:
        raise CompletionVerificationError("scan_order must be an ordered tuple")
    if supplied_order != _REQUIRED_SCANS:
        raise CompletionVerificationError("scan order is incomplete or does not match the AEOS contract")

    scans = scan_results.get("scans")
    if type(scans) is not dict:
        raise CompletionVerificationError("scans must be a mapping")
    if set(scans) != set(_REQUIRED_SCANS):
        raise CompletionVerificationError("every required scan must be present exactly once")
    for name in _REQUIRED_SCANS:
        result = scans[name]
        if type(result) is not dict or type(result.get("status")) is not str or result["status"] != "PASS":
            raise CompletionVerificationError(f"scan is not independently verified: {name}")
        if type(result.get("evidence_refs")) is not tuple or not result["evidence_refs"]:
            raise CompletionVerificationError(f"scan evidence is missing: {name}")

    observations = scan_results.get("observations")
    if type(observations) is not dict:
        raise CompletionVerificationError("observations must be a mapping")
    for name in _REQUIRED_COUNTS:
        value = observations.get(name)
        if type(value) is not int or value < 0:
            raise CompletionVerificationError(f"{name} must be a non-negative integer")
    for name in _REQUIRED_BOOLS:
        if type(observations.get(name)) is not bool:
            raise CompletionVerificationError(f"{name} must be a boolean")

    evidence_payload = {
        "baseline_sha": baseline_sha,
        "scan_order": list(_REQUIRED_SCANS),
        "observations": observations,
        "evidence_refs": list(evidence_refs),
        "scan_evidence_refs": {name: list(scans[name]["evidence_refs"]) for name in _REQUIRED_SCANS},
    }
    digest = _canonical_digest(evidence_payload)

    # Minting is deliberately kept inside the verifier function. There is no
    # public constructor or public factory that callers can invoke to obtain
    # the verifier-issued seal.
    instance = object.__new__(VerifiedCompletionObservation)
    object.__setattr__(instance, "baseline_sha", baseline_sha)
    object.__setattr__(instance, "scan_order", _REQUIRED_SCANS)
    object.__setattr__(instance, "observations", dict(observations))
    object.__setattr__(instance, "evidence_digest", digest)
    object.__setattr__(instance, "_verification_seal", _VERIFICATION_SEAL)
    return instance
