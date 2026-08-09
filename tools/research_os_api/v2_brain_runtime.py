#!/usr/bin/env python3
"""Research OS AI Brain runtime composition.

Phase 4 composes the provider-neutral Brain Core with context assembly, the
versioned Skill Registry, deterministic decision/risk policy, Tool Registry,
secret-aware permissioned execution, Skill -> Tool execution, post-execution
verification, durable checkpoints and the isolated 12-agent Brain engineering
team. The Brain never calls adapters directly.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

from agent_platform import AgentRegistry
from v2_brain_context import ContextEngine, ContextSource
from v2_brain_core import ActivityLedger, ResearchOSBrain, WorkingMemory
from v2_brain_decision import ActionCandidate, DecisionEngine
from v2_brain_team import brain_team_dashboard, register_brain_team
from v2_execution_hardening import (
    HardenedExecutionController,
    SecretAwareCheckpointStore,
    SecretAwareExecutionRequest,
)
from v2_secret_redactor import redaction_status
from v2_skill_executor import SkillExecutionRequest, SkillExecutor
from v2_skill_registry import SkillRegistry
from v2_tool_registry import ToolRegistry


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
        tool_registry: ToolRegistry | None = None,
        checkpoint_store: SecretAwareCheckpointStore | None = None,
        execution_controller: HardenedExecutionController | None = None,
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
        self.tools = tool_registry or ToolRegistry()
        self._attach_internal_tool_adapters()

        if execution_controller is not None:
            self.execution = execution_controller
        else:
            checkpoints = checkpoint_store
            if checkpoints is None and working_memory is not None:
                checkpoints = SecretAwareCheckpointStore(working_memory.root.parent)
            self.execution = HardenedExecutionController(
                tools=self.tools,
                decisions=self.decisions,
                ledger=self.brain.ledger,
                checkpoints=checkpoints,
            )
        self.skill_execution = SkillExecutor(
            skills=self.skills,
            tools=self.tools,
            execution=self.execution,
            brain=self.brain,
        )

    def _attach_internal_tool_adapters(self) -> None:
        def skills_adapter(action: str, payload: Mapping[str, Any], dry_run: bool) -> Mapping[str, Any]:
            del dry_run
            if action == "list":
                items = self.skills.list()
                return {"skills": items, "count": len(items)}
            if action == "discover":
                capability = str(payload.get("capability") or "").strip()
                if not capability:
                    raise ValueError("capability is required")
                matches = self.skills.discover(capability=capability)
                return {"capability": capability, "skills": matches, "count": len(matches)}
            if action == "dashboard":
                return self.skills.dashboard()
            raise ValueError(f"unsupported brain.skills.inspect action: {action}")

        def session_adapter(action: str, payload: Mapping[str, Any], dry_run: bool) -> Mapping[str, Any]:
            del dry_run
            if action != "get":
                raise ValueError(f"unsupported brain.session.inspect action: {action}")
            target = str(payload.get("session_id") or "").strip()
            if not target:
                raise ValueError("session_id is required")
            return self.brain.session(target)

        def context_adapter(action: str, payload: Mapping[str, Any], dry_run: bool) -> Mapping[str, Any]:
            del dry_run
            if action != "build":
                raise ValueError(f"unsupported brain.context.inspect action: {action}")
            objective = str(payload.get("objective") or "").strip()
            if not objective:
                raise ValueError("objective is required")
            raw_context = payload.get("context")
            context = raw_context if isinstance(raw_context, Mapping) else None
            session_id = str(payload.get("session_id") or "").strip() or None
            budget_value = payload.get("budget_chars")
            budget_chars = int(budget_value) if budget_value is not None else None
            return self.build_context(
                objective,
                session_id=session_id,
                context=context,
                budget_chars=budget_chars,
            )

        for tool_id, adapter in (
            ("brain.skills.inspect", skills_adapter),
            ("brain.session.inspect", session_adapter),
            ("brain.context.inspect", context_adapter),
        ):
            try:
                self.tools.register_adapter(tool_id, adapter)
            except ValueError as exc:
                if "already registered" not in str(exc):
                    raise

    def introspect(self) -> dict[str, Any]:
        return {
            "brain": self.brain.introspect(),
            "team": brain_team_dashboard(self.registry),
            "skills": self.skills.dashboard(),
            "tools": self.tools.dashboard(),
            "context": {
                "engine": "authority-provenance-budget",
                "default_budget_chars": self.context.default_budget_chars,
                "secret_redaction": True,
                "long_term_memory_port": type(self.context.memory).__name__,
            },
            "decision_policy": self.decisions.policy(),
            "execution": self.execution.dashboard(),
            "skill_execution": self.skill_execution.dashboard(),
            "secret_redaction": redaction_status(),
            "phase": "brain_core_phase_4",
            "tool_execution": "secret_aware_permissioned_controller_enabled",
            "direct_adapter_access": False,
            "post_execution_verification": True,
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
        tool_matches: dict[str, list[str]] = {}
        for capability in plan.required_capabilities:
            skill_matches[capability] = [
                item["skill_id"] for item in self.skills.discover(capability=capability)
            ]
            tool_matches[capability] = [
                item["tool_id"] for item in self.tools.discover(capability=capability)
            ]
        return {
            "plan": plan,
            "context": context_snapshot,
            "skill_matches": skill_matches,
            "tool_matches": tool_matches,
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

    def discover_tools(self, capability: str, *, ready_only: bool = True) -> list[dict[str, Any]]:
        return self.tools.discover(capability=capability, ready_only=ready_only)

    def match_tools(self, capabilities: Iterable[str]) -> dict[str, Any]:
        return self.tools.match_capabilities(capabilities, ready_only=True)

    def execute_tool(
        self,
        tool_id: str,
        action: str,
        *,
        session_id: str,
        payload: Mapping[str, Any] | None = None,
        granted_permissions: Iterable[str] = (),
        evidence: Mapping[str, Any] | None = None,
        approved: bool = False,
        dry_run: bool = False,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
        secret_values: Iterable[str] = (),
    ) -> dict[str, Any]:
        result = self.execution.execute(
            SecretAwareExecutionRequest(
                session_id=session_id,
                tool_id=tool_id,
                action=action,
                payload=dict(payload or {}),
                granted_permissions=tuple(granted_permissions),
                evidence=dict(evidence or {}),
                approved=approved,
                dry_run=dry_run,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                secret_values=tuple(secret_values),
            )
        )
        return asdict(result)

    def execute_skill(
        self,
        skill_id: str,
        action: str,
        *,
        session_id: str,
        payload: Mapping[str, Any] | None = None,
        granted_permissions: Iterable[str] = (),
        evidence: Mapping[str, Any] | None = None,
        approved: bool = False,
        dry_run: bool = False,
        tool_id: str | None = None,
        idempotency_key: str | None = None,
        correlation_id: str | None = None,
        secret_values: Iterable[str] = (),
    ) -> dict[str, Any]:
        result = self.skill_execution.execute(
            SkillExecutionRequest(
                session_id=session_id,
                skill_id=skill_id,
                action=action,
                payload=dict(payload or {}),
                granted_permissions=tuple(granted_permissions),
                evidence=dict(evidence or {}),
                approved=approved,
                dry_run=dry_run,
                tool_id=tool_id,
                idempotency_key=idempotency_key,
                correlation_id=correlation_id,
                secret_values=tuple(secret_values),
            )
        )
        return asdict(result)


BRAIN_RUNTIME = BrainRuntime()
