"""AEOS constitutional mutation firewall.

Autonomous execution may change governed engineering state, but it cannot
silently change the rules that define its own trust boundary. This module is
a pure decision boundary: it does not grant authority and it does not perform
writes.
"""
from __future__ import annotations

from dataclasses import dataclass


class ConstitutionalFirewallError(ValueError):
    """Raised when a proposed mutation crosses a protected boundary."""


_PROTECTED_PATHS = frozenset(
    {
        "current/AEOS_ASSURANCE_FABRIC_CONTRACT.json",
        "current/AEOS_ASSURANCE_OF_ASSURANCE_CONTRACT.json",
        "current/AEOS_100X_CONTRACT.json",
        "current/AEOS_CERTIFICATE_SCHEMA.json",
    }
)
_PROTECTED_KINDS = frozenset(
    {
        "constitution",
        "trust_anchor",
        "authority_model",
        "evidence_independence_rule",
        "fail_closed_rule",
        "human_approval_boundary",
    }
)


@dataclass(frozen=True)
class ConstitutionalDecision:
    allowed: bool
    reason: str
    requires_governance: bool


def evaluate_constitutional_mutation(
    *,
    paths: tuple[str, ...],
    mutation_kind: str,
    governance_proof: str | None = None,
) -> ConstitutionalDecision:
    """Classify a mutation without granting permission to perform it.

    Protected mutations require an externally issued governance proof. A raw
    caller boolean is deliberately not accepted as authoritative approval.
    """
    if not isinstance(paths, tuple) or not paths or any(not isinstance(path, str) or not path for path in paths):
        raise ConstitutionalFirewallError("mutation paths required")
    if len(set(paths)) != len(paths):
        raise ConstitutionalFirewallError("duplicate mutation path")
    if not isinstance(mutation_kind, str) or not mutation_kind:
        raise ConstitutionalFirewallError("mutation_kind required")
    if governance_proof is not None:
        if not isinstance(governance_proof, str) or len(governance_proof) != 64 or any(c not in "0123456789abcdef" for c in governance_proof):
            raise ConstitutionalFirewallError("invalid governance proof")

    protected = mutation_kind in _PROTECTED_KINDS or bool(_PROTECTED_PATHS.intersection(paths))
    if protected and governance_proof is None:
        return ConstitutionalDecision(False, "governance proof required for protected mutation", True)
    if protected:
        return ConstitutionalDecision(True, "governance proof supplied; external governance must validate it", True)
    return ConstitutionalDecision(True, "mutation is outside protected constitutional boundary", False)
