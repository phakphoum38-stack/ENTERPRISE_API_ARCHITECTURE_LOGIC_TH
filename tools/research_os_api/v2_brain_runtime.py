#!/usr/bin/env python3
"""Research OS AI Brain runtime composition.

The runtime composes provider-neutral cognition, context, capability graph,
domain skills, decision/risk policy, permissioned Tool execution, governed task
orchestration, post-execution verification and safe experience learning. Model
providers remain behind AI Gateway; the Brain never calls adapters directly and
never self-modifies from learned outcomes.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

from agent_platform import AgentRegistry
from v2_brain_context import ContextEngine, ContextSource
from v2_brain_core import ActivityLedger, ResearchOSBrain, WorkingMemory
from v2_brain_decision import ActionCandidate, DecisionEngine
from v2_brain_team import brain_team_dashboard, register_brain_team
from v2_capability_graph import CapabilityGraph
from v2_domain_skills import catalog as domain_skill_catalog
from v2_domain_skills import install_domain_skill_packs
from v2_execution_hardening import (
    HardenedExecutionController,
    SecretAwareCheckpointStore,
    SecretAwareExecutionRequest,
)
from v2_governed_task_runner import GovernedTaskBinding, GovernedTaskRunner
from v2_learning_engine import LearningEngine
from v2_secret_redactor import redaction_status
from v2_skill_executor import SkillExecutionRequest, SkillExecutor
from v2_skill_registry import SkillRegistry
from v2_tool_registry import ToolRegistry


_TERMINAL_TASK_STATES = {"verified", "failed", "blocked", "cancelled", "verification_failed"}


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
        task_runner: GovernedTaskRunner | None = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        register_brain_team(self.registry)
        self.brain = ResearchOSBrain(
            registry=self.registry,
            working_memory=working_memory,
            ledger=ledger,
        )
        self.skills = skill_registry or SkillRegistry()
        if skill_registry is None:
            self.domain_skill_report = install_domain_skill_packs(self.skills)
        else:
            self.domain_skill_report = {
                "contract": domain_skill_catalog()["contract"],
                "packs": [],
                "installed_skill_ids": [],
                "installed_count": 0,
                "total_domain_skills": 0,
                "custom_registry": True,
                "permission_grants": False,
                "tool_adapters_created": False,
            }
        self.context = context_engine or ContextEngine()
        self.decisions = decision_engine or DecisionEngine()
        self.tools = tool_registry or ToolRegistry()
        self._attach_internal_tool_adapters()
        self.capability_graph = CapabilityGraph(
            agents=self.registry,
            skills=self.skills,
            tools=self.tools,
        )
        self.learning = LearningEngine(self.brain.ledger)

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
        self.tasks = task_runner or GovernedTaskRunner(
            brain=self.brain,
            skills=self.skills,
            skill_execution=self.skill_execution,
            ledger=self.brain.ledger,
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
        graph = self.capability_graph.snapshot()
        return {
            "brain": self.brain.introspect(),
            "team": brain_team_dashboard(self.registry),
            "skills": self.skills.dashboard(),
            "domain_skills": {
                **domain_skill_catalog(),
                "runtime_install": self.domain_skill_report,
            },
            "tools": self.tools.dashboard(),
            "capability_graph": {
                "contract": graph["contract"],
                "counts": graph["counts"],
                "persisted": graph["persisted"],
                "duplicate_registry": graph["duplicate_registry"],
            },
            "context": {
                "engine": "authority-provenance-budget",
                "default_budget_chars": self.context.default_budget_chars,
                "secret_redaction": True,
                "long_term_memory_port": type(self.context.memory).__name__,
            },
            "decision_policy": self.decisions.policy(),
            "execution": self.execution.dashboard(),
            "skill_execution": self.skill_execution.dashboard(),
            "task_runner": self.tasks.dashboard(),
            "learning": self.learning.dashboard(),
            "secret_redaction": redaction_status(),
            "phase": "brain_core_phase_10",
            "task_runner_phase": "brain_core_phase_8",
            "learning_phase": "brain_core_phase_9",
            "domain_skills_phase": "brain_core_phase_10",
            "capability_graph_phase": "brain_core_phase_10",
            "tool_execution": "secret_aware_permissioned_controller_enabled",
            "direct_adapter_access": False,
            "post_execution_verification": True,
            "canonical_dependency_graph": "AgentOrchestrator",
            "self_modification": False,
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
            "capability_graph": self.capability_graph.resolve(plan.required_capabilities),
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

    def resolve_capabilities(self, capabilities: Iterable[str]) -> dict[str, Any]:
        return self.capability_graph.resolve(capabilities)

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

    def prepare_task(
        self,
        objective: str,
        *,
        session_id: str,
        bindings: Iterable[GovernedTaskBinding | Mapping[str, Any]],
        context: Mapping[str, Any] | None = None,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        result = self.tasks.prepare(
            objective,
            session_id=session_id,
            bindings=bindings,
            context=context,
            task_id=task_id,
        )
        self._learn_task_if_terminal(result)
        return result

    def start_task(
        self,
        task_id: str,
        *,
        ephemeral_inputs: Mapping[str, Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        result = self.tasks.start(task_id, ephemeral_inputs=ephemeral_inputs)
        self._learn_task_if_terminal(result)
        return result

    def approve_task_step(
        self,
        task_id: str,
        step_id: str,
        *,
        ephemeral_input: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = self.tasks.approve_step(
            task_id,
            step_id,
            ephemeral_input=ephemeral_input,
        )
        self._learn_task_if_terminal(result)
        return result

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self.tasks.get(task_id)

    def task_timeline(self, task_id: str) -> dict[str, Any]:
        return self.tasks.timeline(task_id)

    def cancel_task(self, task_id: str) -> dict[str, Any]:
        result = self.tasks.cancel(task_id)
        self._learn_task_if_terminal(result)
        return result

    def _learn_task_if_terminal(self, record: Mapping[str, Any]) -> None:
        status = str(record.get("status") or "").casefold()
        if status not in _TERMINAL_TASK_STATES:
            return
        task_id = str(record.get("task_id") or "")
        session_id = str(record.get("session_id") or "")
        if not task_id or not session_id:
            return

        # Idempotent projection: repeated get/start calls for a terminal task do
        # not create a second learning event for the same terminal status.
        for event in self.learning.experiences(limit=500):
            payload = event.get("payload") if isinstance(event, Mapping) else None
            if not isinstance(payload, Mapping):
                continue
            if payload.get("task_id") == task_id and payload.get("status") == status:
                return

        plan = record.get("brain_plan") if isinstance(record.get("brain_plan"), Mapping) else {}
        bindings = [item for item in record.get("bindings", ()) if isinstance(item, Mapping)]
        step_results = record.get("step_results") if isinstance(record.get("step_results"), Mapping) else {}
        tool_ids = [
            str(result.get("selected_tool_id"))
            for result in step_results.values()
            if isinstance(result, Mapping) and result.get("selected_tool_id")
        ]
        evidence_refs: list[str] = []
        run_id = str(record.get("orchestration_run_id") or "").strip()
        if run_id:
            evidence_refs.append(f"orchestration:{run_id}")
        for step_id, result in step_results.items():
            if isinstance(result, Mapping) and result.get("status") == "verified":
                evidence_refs.append(f"verified_step:{step_id}")

        failure_category = None
        if status == "verification_failed":
            failure_category = "verification_gap"
        elif status == "blocked":
            failure_category = "capability_permission_or_tool_gap"
        elif status == "failed" and record.get("orchestration_status") == "failed":
            failure_category = "agent_orchestration_failure"
        elif status == "failed":
            failure_category = "skill_or_tool_failure"
        elif status == "cancelled":
            failure_category = "cancelled"

        verification = (
            record.get("final_verification")
            if isinstance(record.get("final_verification"), Mapping)
            else {}
        )
        self.learning.record_experience(
            session_id=session_id,
            task_id=task_id,
            status=status,
            objective=str(record.get("objective") or ""),
            capabilities=tuple(plan.get("required_capabilities") or ()),
            skill_ids=tuple(str(item.get("skill_id")) for item in bindings if item.get("skill_id")),
            tool_ids=tool_ids,
            blockers=tuple(record.get("blocked_reasons") or ()),
            evidence_refs=evidence_refs,
            verification=verification,
            failure_category=failure_category,
        )


BRAIN_RUNTIME = BrainRuntime()
