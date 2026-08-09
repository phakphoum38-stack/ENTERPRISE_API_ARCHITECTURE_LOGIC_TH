#!/usr/bin/env python3
"""Research OS AI Brain runtime composition.

Phase 2 composes the provider-neutral Brain Core with context assembly, the
versioned Skill Registry, deterministic decision/risk policy, the existing Agent
Registry, and the isolated 12-agent Brain engineering team. Tool execution stays
disabled until the permissioned execution-port slice is implemented.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

from agent_platform import AgentRegistry
from v2_brain_context import ContextEngine, ContextSource
from v2_brain_core import ActivityLedger, ResearchOSBrain, WorkingMemory
from v2_brain_decision import ActionCandidate, DecisionEngine
from v2_brain_team import brain_team_dashboard, register_brain_team
from v2_skill_registry import SkillRegistry


class BrainRuntime:
    def __init__(
        self,
        *,
        registry: AgentRegistry | None = None,
        working_memory: WorkingMemory | None = None,
        ledger: ActivityLedger | None = None,
        skill_registry: SkillRegistry | None = None,
        context_engine: ContextEngine | None = None,
        decision_engine: DecisionEngine | None = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        register_brain_team(self.registry)
        self.brain = ResearchOSBrain(
            registry=self.registry,
            working_memory=working_memory,
            ledger=ledger,
        )
        self.skills = skill_registry or SkillRegistry()
        self.context = context_engine or ContextEngine()
        self.decisions = decision_engine or DecisionEngine()

    def introspect(self) -> dict[str, Any]:
        return {
            "brain": self.brain.introspect(),
            "team": brain_team_dashboard(self.registry),
            "skills": self.skills.dashboard(),
            "context": {
                "engine": "authority-provenance-budget",
                "default_budget_chars": self.context.default_budget_chars,
                "secret_redaction": True,
                "long_term_memory_port": type(self.context.memory).__name__,
            },
            "decision_policy": self.decisions.policy(),
            "phase": "brain_core_phase_2",
            "tool_execution": "disabled_until_permissioned_execution_port",
        }

    def build_context(
        self,
        objective: str,
        *,
        session_id: str | None = None,
        context: Mapping[str, Any] | None = None,
        budget_chars: int | None = None,
    ) -> dict[str, Any]:
        sources: list[ContextSource] = [
            ContextSource(
                "brain_identity",
                100,
                {
                    "system": self.brain.identity.system,
                    "brain_component": self.brain.identity.component,
                    "constitution": list(self.brain.constitution.principles),
                    "invariants": list(self.brain.constitution.invariants),
                },
                provenance="brain-core",
                required=True,
            ),
            ContextSource(
                "user_objective",
                95,
                {"objective": objective.strip()},
                provenance="user",
                required=True,
            ),
        ]
        if context:
            sources.append(
                ContextSource(
                    "project_context",
                    80,
                    dict(context),
                    provenance="runtime-input",
                    required=False,
                )
            )
        if session_id:
            state = self.brain.memory.get(session_id)
            if state:
                sources.append(
                    ContextSource(
                        "working_memory",
                        65,
                        {"working_memory": state},
                        provenance="brain-working-memory",
                    )
                )
        snapshot = self.context.build(
            sources,
            objective=objective,
            budget_chars=budget_chars,
        )
        return self.context.as_payload(snapshot)

    def plan(
        self,
        objective: str,
        *,
        session_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        context_snapshot = self.build_context(
            objective,
            session_id=session_id,
            context=context,
        )
        plan = self.brain.plan(objective, session_id=session_id, context=context)
        skill_matches: dict[str, list[str]] = {}
        for capability in plan.required_capabilities:
            skill_matches[capability] = [
                item["skill_id"] for item in self.skills.discover(capability=capability)
            ]
        return {
            "plan": plan,
            "context": context_snapshot,
            "skill_matches": skill_matches,
            "team": brain_team_dashboard(self.registry),
        }

    def evaluate_action(
        self,
        candidates: Iterable[ActionCandidate],
        *,
        granted_permissions: Iterable[str] = (),
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        decision = self.decisions.choose(
            candidates,
            granted_permissions=granted_permissions,
            evidence=evidence,
        )
        return asdict(decision)

    def discover_skills(self, capability: str) -> list[dict[str, Any]]:
        return self.skills.discover(capability=capability)


BRAIN_RUNTIME = BrainRuntime()
