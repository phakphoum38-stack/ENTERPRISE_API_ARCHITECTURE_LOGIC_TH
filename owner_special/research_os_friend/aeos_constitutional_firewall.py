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
    governance_approval: bool = False,
) -> ConstitutionalDecision:
    """Classify a mutation without granting permission to perform it.

    Protected mutations always require explicit governance. Autonomous callers
    cannot turn a governance requirement into an approval flag by self-attesting.
    """
    if not isinstance(paths, tuple) or not paths or any(not isinstance(path, str) or not path for path in paths):
        raise ConstitutionalFirewallError("mutation paths required")
    if len(set(paths)) != len(paths):
        raise ConstitutionalFirewallError("duplicate mutation path")
    if not isinstance(mutation_kind, str) or not mutation_kind:
        raise ConstitutionalFirewallError("mutation_kind required")
    if type(governance_approval) is not bool:
        raise ConstitutionalFirewallError("governance_approval must be bool")

    protected = mutation_kind in _PROTECTED_KINDS or bool(_PROTECTED_PATHS.intersection(paths))
    if protected and not governance_approval:
        return ConstitutionalDecision(False, "governance required for protected mutation", True)
    if protected:
        return ConstitutionalDecision(True, "explicit governance required and present", True)
    return ConstitutionalDecision(True, "mutation is outside protected constitutional boundary", False)
