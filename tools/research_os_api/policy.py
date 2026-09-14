"""Provider-agnostic policy evaluation for Research OS resource governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping

from resource_governance import QuotaDimension, QuotaError, Usage


class PolicyEffect(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    THROTTLE = "throttle"


@dataclass(frozen=True)
class PolicyRule:
    rule_id: str
    effect: PolicyEffect
    dimensions: Mapping[QuotaDimension, int] = field(default_factory=dict)
    required_scopes: frozenset[str] = frozenset()
    principal_types: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise QuotaError("rule_id must not be empty")
        for dimension, limit in self.dimensions.items():
            if not isinstance(dimension, QuotaDimension):
                raise QuotaError("invalid policy dimension")
            if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
                raise QuotaError(f"invalid policy limit: {dimension.value}")
        if any(not scope.strip() for scope in self.required_scopes):
            raise QuotaError("policy scopes must not be empty")
        if any(not principal.strip() for principal in self.principal_types):
            raise QuotaError("policy principal types must not be empty")


@dataclass(frozen=True)
class PolicyContext:
    principal_id: str
    scopes: frozenset[str] = frozenset()
    principal_type: str = "user"

    def __post_init__(self) -> None:
        if not self.principal_id.strip():
            raise QuotaError("principal_id must not be empty")
        if not self.principal_type.strip():
            raise QuotaError("principal_type must not be empty")


@dataclass(frozen=True)
class PolicyDecision:
    effect: PolicyEffect
    rule_id: str
    reason: str
    constrained_usage: Usage | None = None


class PolicyEngine:
    """Deterministic first-match policy engine.

    Policy decides governance intent; quota remains authoritative for capacity.
    """

    def __init__(self) -> None:
        self._rules: list[PolicyRule] = []

    def add_rule(self, rule: PolicyRule) -> None:
        if any(existing.rule_id == rule.rule_id for existing in self._rules):
            raise QuotaError(f"duplicate policy rule: {rule.rule_id}")
        self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> None:
        before = len(self._rules)
        self._rules = [rule for rule in self._rules if rule.rule_id != rule_id]
        if len(self._rules) == before:
            raise QuotaError(f"unknown policy rule: {rule_id}")

    def evaluate(self, context: PolicyContext, usage: Usage) -> PolicyDecision:
        for rule in self._rules:
            if rule.required_scopes and not rule.required_scopes.issubset(context.scopes):
                continue
            if rule.principal_types and context.principal_type not in rule.principal_types:
                continue
            if rule.dimensions and not self._matches_dimensions(rule, usage):
                continue
            return PolicyDecision(rule.effect, rule.rule_id, f"matched:{rule.rule_id}", usage)
        return PolicyDecision(PolicyEffect.ALLOW, "default", "no_matching_rule", usage)

    @staticmethod
    def _matches_dimensions(rule: PolicyRule, usage: Usage) -> bool:
        return all(usage.get(dimension) >= limit for dimension, limit in rule.dimensions.items())

    def snapshot(self) -> tuple[PolicyRule, ...]:
        return tuple(self._rules)
