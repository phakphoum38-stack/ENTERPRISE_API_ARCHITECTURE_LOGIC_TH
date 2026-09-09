"""AEOS authority and risk decision boundary.

Authority is explicit and separate from identity, capability, evidence, and
risk. This module is pure: an external policy/governance adapter must supply
observations; this boundary only validates and combines them.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


class AuthorityRiskError(ValueError):
    """Raised when an authority/risk decision is unsafe or malformed."""


Risk = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL", "IRREVERSIBLE", "SAFETY_CRITICAL", "SECURITY_CRITICAL", "GOVERNANCE_CRITICAL"]

_HIGH_RISK = {"HIGH", "CRITICAL", "IRREVERSIBLE", "SAFETY_CRITICAL", "SECURITY_CRITICAL", "GOVERNANCE_CRITICAL"}


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
        if self.risk in _HIGH_RISK and not self.human_approval:
            raise AuthorityRiskError("high-risk action requires human approval")
        if self.allowed and not self.independently_verified:
            raise AuthorityRiskError("allowed decision requires independent verification")


def evaluate_authority_risk(*, actor: str, authority: str, capability: str, scope: str, risk: Risk, policy_version: str, evidence_refs: tuple[str, ...], authority_verified: bool, capability_verified: bool, provenance_verified: bool, human_approval: bool) -> AuthorityRiskDecision:
    """Evaluate a bounded authority decision without granting authority."""
    for value, label in ((actor, "actor"), (authority, "authority"), (capability, "capability"), (scope, "scope"), (policy_version, "policy_version")):
        if not isinstance(value, str) or not value:
            raise AuthorityRiskError(f"{label} required")
    for value, label in ((authority_verified, "authority_verified"), (capability_verified, "capability_verified"), (provenance_verified, "provenance_verified"), (human_approval, "human_approval")):
        if type(value) is not bool:
            raise AuthorityRiskError(f"{label} must be boolean")
    if not isinstance(evidence_refs, tuple) or not evidence_refs or len(set(evidence_refs)) != len(evidence_refs):
        raise AuthorityRiskError("unique evidence_refs required")
    allowed = authority_verified and capability_verified and provenance_verified
    if risk in _HIGH_RISK:
        allowed = allowed and human_approval
    return AuthorityRiskDecision(actor, authority, capability, scope, risk, policy_version, evidence_refs, True, human_approval, allowed)
