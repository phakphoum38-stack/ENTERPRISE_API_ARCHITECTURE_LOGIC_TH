#!/usr/bin/env python3
"""Unified Research OS V3 Master Orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import agent_server
from brain_skills import BRAIN, BrainSkillsEngine
from v2_brain_runtime import BRAIN_RUNTIME, BrainRuntime
from v2_system_introspection import SystemIntrospection
from v2_tool_intelligence import ToolIntelligence

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from software_factory import AdaptiveControlPlane, SUPPORTED_PROFILES  # noqa: E402


UNIFIED_MASTER_CONTRACT = "unified-master-orchestrator-v3"
UNIFIED_VERSION = "v3-unified"
_MAX_ACTIVE_VERSION_FACTORIES = 1296


class UnifiedMasterOrchestrator:
    """Single composition owner for governed intelligence and adaptive execution."""

    def __init__(
        self,
        repository_root: Path | None = None,
        *,
        brain_runtime: BrainRuntime | None = None,
        compound_brain: BrainSkillsEngine | None = None,
    ) -> None:
        self.repository_root = (repository_root or _REPO_ROOT).resolve()
        self.brain_runtime = brain_runtime or BRAIN_RUNTIME
        self.compound_brain = compound_brain or BRAIN
        self.agent_orchestrator = agent_server.ORCHESTRATOR
        self.operational_registry = agent_server.REGISTRY
        self.intelligence = SystemIntrospection(
            self.brain_runtime,
            self.operational_registry,
        )
        self.tool_intelligence = ToolIntelligence(
            self.brain_runtime.tools,
            self.brain_runtime.learning,
        )
        self.factory_control = AdaptiveControlPlane(self.repository_root)

    def manifest(self) -> dict[str, Any]:
        capacity = self.compound_brain.capacity_snapshot()
        return {
            "contract": UNIFIED_MASTER_CONTRACT,
            "version": UNIFIED_VERSION,
            "architecture": "adaptive_hierarchical_ai_software_factory",
            "single_master_owner": True,
            "owners": {
                "master": "UnifiedMasterOrchestrator",
                "governed_brain_core": "v2_brain_runtime.BRAIN_RUNTIME",
                "compound_brain": "brain_skills.BRAIN",
                "agent_dependency_graph": "agent_server.ORCHESTRATOR",
                "tool_registry": "BrainRuntime.tools",
                "tool_intelligence": "v2_tool_intelligence.ToolIntelligence",
                "tool_learning": "BrainRuntime.learning",
                "factory_control": "software_factory.AdaptiveControlPlane",
                "provider_gateway": "existing provider gateway",
            },
            "factory_profiles": [profile.label for profile in SUPPORTED_PROFILES],
            "capacity": capacity,
            "invariants": {
                "canonical_dependency_graph": "AgentOrchestrator",
                "duplicate_dependency_graph": False,
                "lazy_activation": True,
                "all_workers_started_by_default": False,
                "writes_require_approval": True,
                "external_tools_auto_downloaded": False,
                "external_tools_auto_installed": False,
                "external_tools_auto_executed": False,
                "self_modification": False,
                "automatic_merge_release_deploy": False,
            },
        }

    def status(self) -> dict[str, Any]:
        runtime = self.brain_runtime.introspect()
        return {
            **self.manifest(),
            "brain_runtime": runtime,
            "tool_intelligence": self.tool_intelligence.dashboard(),
            "factory": self.factory_control.summary(),
            "intelligence_health": self.intelligence.health(),
        }

    def plan(
        self,
        objective: str,
        *,
        session_id: str | None = None,
        context: Mapping[str, Any] | None = None,
        complexity_level: int | None = None,
        requested_workers: int | None = None,
        budget_workers: int | None = None,
        ready_workers: int | None = None,
        versions: Sequence[str] = (UNIFIED_VERSION,),
    ) -> dict[str, Any]:
        text = objective.strip()
        if not text:
            raise ValueError("objective is required")

        normalized_versions = tuple(
            dict.fromkeys(str(version).strip() for version in versions if str(version).strip())
        )
        if not normalized_versions:
            normalized_versions = (UNIFIED_VERSION,)
        if len(normalized_versions) > _MAX_ACTIVE_VERSION_FACTORIES:
            raise ValueError(
                f"versions must not exceed {_MAX_ACTIVE_VERSION_FACTORIES} active factories per request"
            )

        safe_context = dict(context or {})
        compound_plan = self.compound_brain.plan(
            text,
            complexity_level=complexity_level,
            requested_workers=requested_workers,
            budget_workers=budget_workers,
            ready_workers=ready_workers,
        )
        governed_plan = self.intelligence.plan(
            text,
            session_id=session_id,
            context=safe_context,
        )
        tool_strategy = self.tool_intelligence.plan_for_objective(text, context=safe_context)
        if self.tool_intelligence.should_discover(text):
            provider_name = str(safe_context.get("tool_search_provider") or "").strip() or None
            model = str(safe_context.get("tool_search_model") or "").strip() or None
            tool_strategy = {
                **tool_strategy,
                "external_discovery": self.tool_intelligence.discover(
                    text,
                    capabilities=tool_strategy.get("required_capabilities") or (),
                    provider_name=provider_name,
                    model=model,
                ),
            }

        factory_plan = self.factory_control.configure_versions(normalized_versions)
        return {
            "contract": UNIFIED_MASTER_CONTRACT,
            "version": UNIFIED_VERSION,
            "objective": text,
            "compound_brain": compound_plan,
            "governed_brain": governed_plan,
            "tool_intelligence": tool_strategy,
            "factory": {
                "profile": factory_plan.profile.label,
                "logical_capacity": factory_plan.profile.capacity,
                "requested_factories": factory_plan.requested_factories,
                "active_factories": factory_plan.active_factories,
                "active_orchestrators": factory_plan.active_orchestrators,
                "versions": list(normalized_versions),
            },
            "execution": {
                "performed": False,
                "approval_bypassed": False,
                "external_tool_installed": False,
                "external_tool_executed": False,
                "canonical_dependency_graph": "AgentOrchestrator",
                "lazy_activation": True,
            },
        }

    def discover_tools(
        self,
        objective: str,
        *,
        capabilities: Sequence[str] = (),
        provider_name: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        return self.tool_intelligence.discover(
            objective,
            capabilities=capabilities,
            provider_name=provider_name,
            model=model,
        )

    def design_tool_adapter(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        return self.tool_intelligence.design_adapter(candidate)

    def tool_playbook(self, tool_id: str) -> dict[str, Any]:
        return self.tool_intelligence.tool_playbook(tool_id)


MASTER = UnifiedMasterOrchestrator()


__all__ = [
    "MASTER",
    "UNIFIED_MASTER_CONTRACT",
    "UNIFIED_VERSION",
    "UnifiedMasterOrchestrator",
]
