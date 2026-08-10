#!/usr/bin/env python3
"""Unified Research OS V3 Master Orchestrator.

This module composes the existing V2 governed Brain Runtime, V3 adaptive
Compound Brain, canonical AgentOrchestrator, and Adaptive Software Factory.
It does not create a second dependency graph, bypass approvals, or eagerly
materialize the theoretical 6^6 hierarchy.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import agent_server
from brain_skills import BRAIN, BrainSkillsEngine
from v2_brain_runtime import BRAIN_RUNTIME, BrainRuntime
from v2_system_introspection import SystemIntrospection

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
                "self_modification": False,
                "automatic_merge_release_deploy": False,
            },
        }

    def status(self) -> dict[str, Any]:
        runtime = self.brain_runtime.introspect()
        return {
            **self.manifest(),
            "brain_runtime": runtime,
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
            context=dict(context or {}),
        )
        factory_plan = self.factory_control.configure_versions(normalized_versions)

        return {
            "contract": UNIFIED_MASTER_CONTRACT,
            "version": UNIFIED_VERSION,
            "objective": text,
            "compound_brain": compound_plan,
            "governed_brain": governed_plan,
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
                "canonical_dependency_graph": "AgentOrchestrator",
                "lazy_activation": True,
            },
        }


MASTER = UnifiedMasterOrchestrator()


__all__ = [
    "MASTER",
    "UNIFIED_MASTER_CONTRACT",
    "UNIFIED_VERSION",
    "UnifiedMasterOrchestrator",
]
