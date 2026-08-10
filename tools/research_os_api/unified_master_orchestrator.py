#!/usr/bin/env python3
"""Unified Research OS V3 Master Orchestrator.

This module composes the existing V2 governed Brain Runtime, V3 adaptive
Compound Brain, canonical AgentOrchestrator, Adaptive Software Factory, the
governed Tool Intelligence layer, a separate Cyber Web Security Standard owner,
and an explicit File Ownership boundary owner. It does not create a second
dependency graph, bypass approvals, auto-install discovered software, or eagerly
materialize the theoretical 6^6 hierarchy.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import agent_server
from brain_skills import BRAIN, BrainSkillsEngine
from v2_brain_runtime import BRAIN_RUNTIME, BrainRuntime
from v2_cyber_web_standard import CYBER_WEB_STANDARD, CyberWebSecurityStandard
from v2_file_ownership_boundary import FILE_OWNERSHIP, FileOwnershipBoundary
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
        cyber_web_security: CyberWebSecurityStandard | None = None,
        file_ownership: FileOwnershipBoundary | None = None,
    ) -> None:
        self.repository_root = (repository_root or _REPO_ROOT).resolve()
        self.brain_runtime = brain_runtime or BRAIN_RUNTIME
        self.compound_brain = compound_brain or BRAIN
        self.cyber_web_security = cyber_web_security or CYBER_WEB_STANDARD
        self.file_ownership = file_ownership or FILE_OWNERSHIP
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
        cyber_boundary = self.cyber_web_security.ownership_boundary()
        file_boundary = self.file_ownership.cyber_boundary()
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
                "cyber_web_security": "v2_cyber_web_standard.CyberWebSecurityStandard",
                "file_ownership": "v2_file_ownership_boundary.FileOwnershipBoundary",
                "factory_control": "software_factory.AdaptiveControlPlane",
                "provider_gateway": "existing provider gateway",
            },
            "owner_boundaries": {
                "cyber_web_security": cyber_boundary,
                "file_ownership": file_boundary,
                "shared_authority": False,
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
                "cyber_security_separate_from_file_ownership": True,
                "cyber_security_can_change_file_owner": False,
                "cyber_security_can_grant_file_acl": False,
                "file_ownership_can_override_cyber_policy": False,
                "file_ownership_can_disable_security_controls": False,
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
            "cyber_web_security": self.cyber_web_security.manifest(),
            "file_ownership": self.file_ownership.manifest(),
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
        tool_strategy = self.tool_intelligence.plan_for_objective(
            text,
            context=safe_context,
        )
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
            "cyber_web_security": {
                "contract": self.cyber_web_security.manifest()["contract"],
                "owner": "CyberWebSecurityStandard",
                "separate_from_file_owner_system": True,
                "assessment_performed": False,
                "changes_file_ownership": False,
                "grants_file_acl": False,
            },
            "file_ownership": self.file_ownership.plan(),
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
                "file_owner_changed": False,
                "file_acl_granted": False,
                "canonical_dependency_graph": "AgentOrchestrator",
                "lazy_activation": True,
            },
        }

    def assess_cyber_web_security(
        self,
        evidence: Mapping[str, Any],
        *,
        deployment_mode: str = "public",
    ) -> dict[str, Any]:
        """Evaluate web/API security evidence without touching file ownership."""
        return self.cyber_web_security.assess(
            evidence,
            deployment_mode=deployment_mode,
        )

    def file_ownership_status(self) -> dict[str, Any]:
        """Expose the separate file-ownership boundary without mutating files."""
        return self.file_ownership.manifest()

    def discover_tools(
        self,
        objective: str,
        *,
        capabilities: Sequence[str] = (),
        provider_name: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        """Research external tool candidates without downloading or executing them."""
        return self.tool_intelligence.discover(
            objective,
            capabilities=capabilities,
            provider_name=provider_name,
            model=model,
        )

    def design_tool_adapter(self, candidate: Mapping[str, Any]) -> dict[str, Any]:
        """Create a reviewable integration plan; never writes adapter code automatically."""
        return self.tool_intelligence.design_adapter(candidate)

    def tool_playbook(self, tool_id: str) -> dict[str, Any]:
        """Summarize structured observed outcomes for an already-registered tool."""
        return self.tool_intelligence.tool_playbook(tool_id)


MASTER = UnifiedMasterOrchestrator()


__all__ = [
    "MASTER",
    "UNIFIED_MASTER_CONTRACT",
    "UNIFIED_VERSION",
    "UnifiedMasterOrchestrator",
]
