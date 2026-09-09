"""AEOS authority and risk decision boundary.

Authority is separate from identity, capability, evidence, and risk. The
boundary accepts only an explicit verification proof produced from a
canonicalized observation; raw caller booleans are intentionally rejected.
The proof is bound to the exact baseline, policy, evidence root, provenance
root, and evidence references it claims to verify. Human approval is bound to
the canonical ApprovalGate through ApprovalProof for high-risk decisions.
This module never grants or escalates authority and does not implement an
independent provenance verifier.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Literal, Mapping, Any

from .approval import ApprovalProof, ApprovalState


class AuthorityRiskError(ValueError):
    """Raised when an authority/risk decision is unsafe or malformed."""


Risk = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL", "IRREVERSIBLE", "SAFETY_CRITICAL", "SECURITY_CRITICAL", "GOVERNANCE_CRITICAL"]
_ALLOWED_RISKS = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL", "IRREVERSIBLE", "SAFETY_CRITICAL", "SECURITY_CRITICAL", "GOVERNANCE_CRITICAL"})
_HIGH_RISK = _ALLOWED_RISKS - {"LOW", "MEDIUM"}


def _require_sha(value: Any, length: int, label: str) -> str:
    if not isinstance(value, str) or not (len(value) == length and re.fullmatch(r"[0-9a-f]+", value)):
        raise AuthorityRiskError(f"{label} must be lowercase hexadecimal SHA-{length * 4}")
    return value


def _canonical_digest(payload: Mapping[str, Any]) -> str:
    try:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AuthorityRiskError("verification proof must be canonicalizable") from exc
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class AuthorityVerificationProof:
    """Canonical proof boundary for authority/capability/provenance claims."""

    authority_verified: bool
    capability_verified: bool
    provenance_verified: bool
    baseline_sha: str
    policy_version: str
    policy_sha256: str
    evidence_root: str
    provenance_root: str
    evidence_refs: tuple[str, ...]
    verifier_id: str
    evidence_digest: str

    def __post_init__(self) -> None:
        for name, value in (("authority_verified", self.authority_verified), ("capability_verified", self.capability_verified), ("provenance_verified", self.provenance_verified)):
            if type(value) is not bool:
                raise AuthorityRiskError(f"{name} must be boolean")
        _require_sha(self.baseline_sha, 40, "baseline_sha")
        _require_sha(self.policy_sha256, 64, "policy_sha256")
        _require_sha(self.evidence_root, 64, "evidence_root")
        _require_sha(self.provenance_root, 64, "provenance_root")
        if not isinstance(self.policy_version, str) or not self.policy_version:
            raise AuthorityRiskError("policy_version required")
        if not isinstance(self.verifier_id, str) or not self.verifier_id:
            raise AuthorityRiskError("verifier_id required")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs or len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise AuthorityRiskError("unique evidence_refs required")
        if any(not isinstance(ref, str) or not ref for ref in self.evidence_refs):
            raise AuthorityRiskError("invalid evidence reference")
        _require_sha(self.evidence_digest, 64, "evidence_digest")


def build_authority_verification_proof(
    *,
    authority_verified: bool,
    capability_verified: bool,
    provenance_verified: bool,
    baseline_sha: str,
    policy_version: str,
    policy_sha256: str,
    evidence_root: str,
    provenance_root: str,
    evidence_refs: tuple[str, ...],
    verifier_id: str,
) -> AuthorityVerificationProof:
    """Build a deterministic proof envelope from verifier observations.

    A governance/external verifier remains responsible for establishing the
    observations and for ensuring the supplied roots identify the canonical
    evidence/provenance records. This function only canonicalizes and binds
    those observations so downstream decisions cannot silently replace or
    omit the proof. It is deliberately not a provenance verifier.
    """
    payload: Mapping[str, Any] = {
        "authority_verified": authority_verified,
        "baseline_sha": baseline_sha,
        "capability_verified": capability_verified,
        "evidence_refs": list(evidence_refs),
        "evidence_root": evidence_root,
        "policy_sha256": policy_sha256,
        "policy_version": policy_version,
        "provenance_root": provenance_root,
        "provenance_verified": provenance_verified,
        "verifier_id": verifier_id,
    }
    return AuthorityVerificationProof(
        authority_verified=authority_verified,
        capability_verified=capability_verified,
        provenance_verified=provenance_verified,
        baseline_sha=baseline_sha,
        policy_version=policy_version,
        policy_sha256=policy_sha256,
        evidence_root=evidence_root,
        provenance_root=provenance_root,
        evidence_refs=evidence_refs,
        verifier_id=verifier_id,
        evidence_digest=_canonical_digest(payload),
    )


@dataclass(frozen=True)
class AuthorityRiskDecision:
    actor: str
    authority: str
    capability: str
    scope: str
    risk: Risk
    baseline_sha: str
    policy_version: str
    policy_sha256: str
    evidence_root: str
    provenance_root: str
    evidence_refs: tuple[str, ...]
    independently_verified: bool
    human_approval: bool
    allowed: bool
    verification_digest: str

    def __post_init__(self) -> None:
        for name, value in (("actor", self.actor), ("authority", self.authority), ("capability", self.capability), ("scope", self.scope), ("policy_version", self.policy_version)):
            if not isinstance(value, str) or not value:
                raise AuthorityRiskError(f"{name} required")
        if self.risk not in _ALLOWED_RISKS:
            raise AuthorityRiskError("invalid risk")
        _require_sha(self.baseline_sha, 40, "baseline_sha")
        _require_sha(self.policy_sha256, 64, "policy_sha256")
        _require_sha(self.evidence_root, 64, "evidence_root")
        _require_sha(self.provenance_root, 64, "provenance_root")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs or len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise AuthorityRiskError("unique evidence_refs required")
        if any(not isinstance(ref, str) or not ref for ref in self.evidence_refs):
            raise AuthorityRiskError("invalid evidence reference")
        if type(self.independently_verified) is not bool or type(self.human_approval) is not bool or type(self.allowed) is not bool:
            raise AuthorityRiskError("boolean fields must be strict booleans")
        _require_sha(self.verification_digest, 64, "verification_digest")
        if self.risk in _HIGH_RISK and not self.human_approval:
            raise AuthorityRiskError("high-risk action requires human approval")
        if self.allowed and not self.independently_verified:
            raise AuthorityRiskError("allowed decision requires independent verification")


def evaluate_authority_risk(
    *, actor: str, authority: str, capability: str, scope: str, risk: Risk,
    baseline_sha: str, policy_version: str, policy_sha256: str,
    evidence_root: str, provenance_root: str, evidence_refs: tuple[str, ...],
    human_approval: bool, verification_proof: AuthorityVerificationProof,
    approval_proof: ApprovalProof | None = None,
) -> AuthorityRiskDecision:
    """Evaluate a bounded authority decision from explicit verification proofs.

    ``human_approval`` is retained for compatibility but is never sufficient
    for high-risk decisions. High-risk approval must come from the canonical
    ApprovalGate as an APPROVED ApprovalProof bound to the exact request.
    """
    for value, label in ((actor, "actor"), (authority, "authority"), (capability, "capability"), (scope, "scope"), (policy_version, "policy_version")):
        if not isinstance(value, str) or not value:
            raise AuthorityRiskError(f"{label} required")
    if risk not in _ALLOWED_RISKS:
        raise AuthorityRiskError("invalid risk")
    _require_sha(baseline_sha, 40, "baseline_sha")
    _require_sha(policy_sha256, 64, "policy_sha256")
    _require_sha(evidence_root, 64, "evidence_root")
    _require_sha(provenance_root, 64, "provenance_root")
    if not isinstance(evidence_refs, tuple) or not evidence_refs or len(set(evidence_refs)) != len(evidence_refs):
        raise AuthorityRiskError("unique evidence_refs required")
    if any(not isinstance(ref, str) or not ref for ref in evidence_refs):
        raise AuthorityRiskError("invalid evidence reference")
    if type(human_approval) is not bool:
        raise AuthorityRiskError("human_approval must be boolean")
    if not isinstance(verification_proof, AuthorityVerificationProof):
        raise AuthorityRiskError("verification_proof required")
    if verification_proof.baseline_sha != baseline_sha:
        raise AuthorityRiskError("verification baseline mismatch")
    if verification_proof.policy_version != policy_version:
        raise AuthorityRiskError("verification policy version mismatch")
    if verification_proof.policy_sha256 != policy_sha256:
        raise AuthorityRiskError("verification policy digest mismatch")
    if verification_proof.evidence_root != evidence_root:
        raise AuthorityRiskError("verification evidence root mismatch")
    if verification_proof.provenance_root != provenance_root:
        raise AuthorityRiskError("verification provenance root mismatch")
    if verification_proof.evidence_refs != evidence_refs:
        raise AuthorityRiskError("verification evidence mismatch")

    approved = False
    if approval_proof is not None:
        if not isinstance(approval_proof, ApprovalProof):
            raise AuthorityRiskError("invalid approval proof")
        if approval_proof.state is not ApprovalState.APPROVED:
            raise AuthorityRiskError("approval proof is not approved")
        if not approval_proof.is_integrity_valid():
            raise AuthorityRiskError("approval proof integrity mismatch")
        approved = True

    allowed = (
        verification_proof.authority_verified
        and verification_proof.capability_verified
        and verification_proof.provenance_verified
    )
    if risk in _HIGH_RISK:
        if not approved:
            raise AuthorityRiskError("high-risk action requires canonical ApprovalGate proof")
        allowed = allowed and approved
    return AuthorityRiskDecision(
        actor, authority, capability, scope, risk, baseline_sha, policy_version,
        policy_sha256, evidence_root, provenance_root, evidence_refs,
        True, approved, allowed, verification_proof.evidence_digest,
    )
