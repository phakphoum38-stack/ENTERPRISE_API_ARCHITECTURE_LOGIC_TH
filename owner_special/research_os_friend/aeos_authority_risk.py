"""AEOS authority and risk decision boundary.

Authority is separate from identity, capability, evidence, and risk. The
boundary accepts only an explicit verification proof produced from a
canonicalized observation; raw caller booleans are intentionally rejected.
This module never grants or escalates authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Mapping, Any


class AuthorityRiskError(ValueError):
    """Raised when an authority/risk decision is unsafe or malformed."""


Risk = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL", "IRREVERSIBLE", "SAFETY_CRITICAL", "SECURITY_CRITICAL", "GOVERNANCE_CRITICAL"]

_HIGH_RISK = {"HIGH", "CRITICAL", "IRREVERSIBLE", "SAFETY_CRITICAL", "SECURITY_CRITICAL", "GOVERNANCE_CRITICAL"}


@dataclass(frozen=True)
class AuthorityVerificationProof:
    """Canonical proof boundary for authority/capability/provenance claims."""

    authority_verified: bool
    capability_verified: bool
    provenance_verified: bool
    policy_version: str
    evidence_refs: tuple[str, ...]
    verifier_id: str
    evidence_digest: str

    def __post_init__(self) -> None:
        for name, value in (("authority_verified", self.authority_verified), ("capability_verified", self.capability_verified), ("provenance_verified", self.provenance_verified)):
            if type(value) is not bool:
                raise AuthorityRiskError(f"{name} must be boolean")
        if not isinstance(self.policy_version, str) or not self.policy_version:
            raise AuthorityRiskError("policy_version required")
        if not isinstance(self.verifier_id, str) or not self.verifier_id:
            raise AuthorityRiskError("verifier_id required")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs or len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise AuthorityRiskError("unique evidence_refs required")
        if any(not isinstance(ref, str) or not ref for ref in self.evidence_refs):
            raise AuthorityRiskError("invalid evidence reference")
        if not isinstance(self.evidence_digest, str) or len(self.evidence_digest) != 64 or any(ch not in "0123456789abcdef" for ch in self.evidence_digest):
            raise AuthorityRiskError("invalid evidence_digest")


def build_authority_verification_proof(
    *,
    authority_verified: bool,
    capability_verified: bool,
    provenance_verified: bool,
    policy_version: str,
    evidence_refs: tuple[str, ...],
    verifier_id: str,
) -> AuthorityVerificationProof:
    """Build a deterministic proof envelope from verifier observations.

    A governance/external verifier remains responsible for establishing the
    observations. This function only canonicalizes the evidence so downstream
    decisions cannot silently replace or omit the proof.
    """
    payload: Mapping[str, Any] = {
        "authority_verified": authority_verified,
        "capability_verified": capability_verified,
        "provenance_verified": provenance_verified,
        "policy_version": policy_version,
        "evidence_refs": list(evidence_refs),
        "verifier_id": verifier_id,
    }
    try:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AuthorityRiskError("verification proof must be canonicalizable") from exc
    return AuthorityVerificationProof(
        authority_verified=authority_verified,
        capability_verified=capability_verified,
        provenance_verified=provenance_verified,
        policy_version=policy_version,
        evidence_refs=evidence_refs,
        verifier_id=verifier_id,
        evidence_digest=hashlib.sha256(encoded).hexdigest(),
    )


@dataclass(frozen=True)
class AuthorityRiskDecision:
    actor: str
    authority: str
    capability: str
    scope: str
    risk: Risk
    policy_version: str
    evidence_refs: tuple[str, ...]
    independently_verified: bool
    human_approval: bool
    allowed: bool
    verification_digest: str

    def __post_init__(self) -> None:
        for name, value in (("actor", self.actor), ("authority", self.authority), ("capability", self.capability), ("scope", self.scope), ("policy_version", self.policy_version)):
            if not isinstance(value, str) or not value:
                raise AuthorityRiskError(f"{name} required")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs or len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise AuthorityRiskError("unique evidence_refs required")
        if any(not isinstance(ref, str) or not ref for ref in self.evidence_refs):
            raise AuthorityRiskError("invalid evidence reference")
        if type(self.independently_verified) is not bool or type(self.human_approval) is not bool or type(self.allowed) is not bool:
            raise AuthorityRiskError("boolean fields must be strict booleans")
        if not isinstance(self.verification_digest, str) or len(self.verification_digest) != 64:
            raise AuthorityRiskError("verification_digest required")
        if self.risk in _HIGH_RISK and not self.human_approval:
            raise AuthorityRiskError("high-risk action requires human approval")
        if self.allowed and not self.independently_verified:
            raise AuthorityRiskError("allowed decision requires independent verification")


def evaluate_authority_risk(
    *, actor: str, authority: str, capability: str, scope: str, risk: Risk,
    policy_version: str, evidence_refs: tuple[str, ...], human_approval: bool,
    verification_proof: AuthorityVerificationProof,
) -> AuthorityRiskDecision:
    """Evaluate a bounded authority decision from an explicit verification proof."""
    for value, label in ((actor, "actor"), (authority, "authority"), (capability, "capability"), (scope, "scope"), (policy_version, "policy_version")):
        if not isinstance(value, str) or not value:
            raise AuthorityRiskError(f"{label} required")
    if type(human_approval) is not bool:
        raise AuthorityRiskError("human_approval must be boolean")
    if not isinstance(verification_proof, AuthorityVerificationProof):
        raise AuthorityRiskError("verification_proof required")
    if verification_proof.policy_version != policy_version:
        raise AuthorityRiskError("verification policy version mismatch")
    if verification_proof.evidence_refs != evidence_refs:
        raise AuthorityRiskError("verification evidence mismatch")

    allowed = (
        verification_proof.authority_verified
        and verification_proof.capability_verified
        and verification_proof.provenance_verified
    )
    if risk in _HIGH_RISK:
        allowed = allowed and human_approval
    return AuthorityRiskDecision(
        actor, authority, capability, scope, risk, policy_version, evidence_refs,
        True, human_approval, allowed, verification_proof.evidence_digest,
    )
