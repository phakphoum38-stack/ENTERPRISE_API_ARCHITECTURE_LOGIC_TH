#!/usr/bin/env python3
"""Research OS AI Brain decision and risk engine.

The engine exposes concise, auditable decision summaries. It does not expose
hidden chain-of-thought. Risk and approval policy remain deterministic so model
choice cannot silently relax Research OS governance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ActionCandidate:
    action_id: str
    description: str
    state_change: bool = False
    destructive: bool = False
    network: bool = False
    secret_access: bool = False
    release_boundary: bool = False
    production_boundary: bool = False
    required_permissions: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    utility: int = 0


@dataclass(frozen=True)
class RiskAssessment:
    score: int
    level: str
    signals: tuple[str, ...]
    approval_required: bool
    blocked: bool
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class DecisionSummary:
    selected_action_id: str | None
    decision: str
    risk: RiskAssessment | None
    alternatives: tuple[dict[str, Any], ...]
    reason: str


class DecisionEngine:
    def assess(
        self,
        candidate: ActionCandidate,
        *,
        granted_permissions: Iterable[str] = (),
        evidence: Mapping[str, Any] | None = None,
    ) -> RiskAssessment:
        permissions = {item.strip().casefold() for item in granted_permissions if item.strip()}
        evidence = dict(evidence or {})
        score = 0
        signals: list[str] = []
        blocked: list[str] = []

        def add(value: int, signal: str) -> None:
            nonlocal score
            score += value
            signals.append(signal)

        if candidate.state_change:
            add(2, "state_change")
        if candidate.network:
            add(1, "network")
        if candidate.secret_access:
            add(3, "secret_access")
        if candidate.destructive:
            add(5, "destructive")
        if candidate.release_boundary:
            add(5, "release_boundary")
        if candidate.production_boundary:
            add(6, "production_boundary")

        for permission in candidate.required_permissions:
            normalized = permission.casefold().strip()
            if normalized.endswith(".prohibited") or normalized == "prohibited":
                blocked.append(f"permission prohibited: {permission}")
            elif normalized not in permissions:
                blocked.append(f"permission missing: {permission}")

        for name in candidate.required_evidence:
            if name not in evidence or evidence[name] in (None, "", [], {}):
                blocked.append(f"evidence missing: {name}")

        if score <= 2:
            level = "low"
        elif score <= 5:
            level = "medium"
        elif score <= 8:
            level = "high"
        else:
            level = "critical"

        approval_required = bool(
            candidate.state_change
            and (
                score >= 3
                or candidate.destructive
                or candidate.secret_access
                or candidate.release_boundary
                or candidate.production_boundary
            )
        )
        return RiskAssessment(
            score=score,
            level=level,
            signals=tuple(signals),
            approval_required=approval_required,
            blocked=bool(blocked),
            blocked_reasons=tuple(blocked),
        )

    def choose(
        self,
        candidates: Iterable[ActionCandidate],
        *,
        granted_permissions: Iterable[str] = (),
        evidence: Mapping[str, Any] | None = None,
    ) -> DecisionSummary:
        assessed: list[tuple[ActionCandidate, RiskAssessment]] = []
        for candidate in candidates:
            assessed.append(
                (
                    candidate,
                    self.assess(
                        candidate,
                        granted_permissions=granted_permissions,
                        evidence=evidence,
                    ),
                )
            )
        if not assessed:
            return DecisionSummary(None, "blocked", None, (), "no action candidates")

        allowed = [item for item in assessed if not item[1].blocked]
        alternatives = tuple(
            {
                "action_id": candidate.action_id,
                "risk": asdict(risk),
                "utility": candidate.utility,
            }
            for candidate, risk in assessed
        )
        if not allowed:
            return DecisionSummary(
                None,
                "blocked",
                None,
                alternatives,
                "all action candidates are blocked by permission or evidence requirements",
            )

        # Prefer lower risk, then higher utility, then stable action id.
        selected, risk = sorted(
            allowed,
            key=lambda item: (item[1].score, -item[0].utility, item[0].action_id),
        )[0]
        decision = "approval_required" if risk.approval_required else "allowed"
        return DecisionSummary(
            selected.action_id,
            decision,
            risk,
            alternatives,
            "selected the lowest-risk permitted candidate; utility breaks equal-risk ties",
        )

    @staticmethod
    def policy() -> dict[str, Any]:
        return {
            "engine": "deterministic-risk-policy",
            "hidden_chain_of_thought": False,
            "selection_order": ["not_blocked", "lowest_risk", "highest_utility", "stable_id"],
            "approval": "state-changing elevated-risk actions require approval",
            "production_release": "always elevated and evidence/permission gated",
        }
