#!/usr/bin/env python3
"""Research OS AI Brain system introspection contract.

Phase 7 makes the runtime's own structure queryable without granting execution
authority. It composes existing registries rather than inventing a second source
of truth. Responses are secret-safe, bounded, and explicit about what is known,
ready, unavailable, or not authoritative at runtime.
"""

from __future__ import annotations

import os
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable, Mapping

from agent_platform import AgentRegistry
from v2_brain_runtime import BrainRuntime
from v2_brain_team import BRAIN_TEAM_IDS
from v2_secret_redactor import sanitize_external


SYSTEM_INTROSPECTION_CONTRACT = "brain-system-introspection-phase-7"
_MAX_OBJECTIVE_CHARS = 8_000
_MAX_CONTEXT_CHARS = 64_000
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _bool_query(value: str | None, *, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().casefold() not in {"0", "false", "no", "off"}


def _unique_sorted(values: Iterable[str]) -> list[str]:
    return sorted({str(value) for value in values if str(value).strip()})


class SystemIntrospection:
    """Read-only facade over the canonical runtime registries."""

    def __init__(self, runtime: BrainRuntime, operational_registry: AgentRegistry) -> None:
        self.runtime = runtime
        self.operational_registry = operational_registry

    def manifest(self) -> dict[str, Any]:
        health = self.health()
        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "system": "Research OS",
            "component": "AI Brain System Introspection",
            "read_only": True,
            "execution_authority": False,
            "hidden_chain_of_thought_exposed": False,
            "sources_of_truth": {
                "operational_agents": "agent_platform.REGISTRY",
                "brain_team": "v2_brain_team.BRAIN_TEAM",
                "skills": "BrainRuntime.skills",
                "tools": "BrainRuntime.tools",
                "execution_policy": "BrainRuntime.execution",
                "provider_selection": "AI Gateway",
                "orchestration": "AgentOrchestrator",
                "workspace_knowledge": "WorkspaceKnowledgeEngine",
            },
            "counts": health["counts"],
            "ready": health["ready"],
            "safety": self._safety_boundary(),
            "endpoints": [
                "/v2/intelligence",
                "/v2/intelligence/capabilities",
                "/v2/intelligence/agents",
                "/v2/intelligence/skills",
                "/v2/intelligence/tools",
                "/v2/intelligence/permissions",
                "/v2/intelligence/architecture",
                "/v2/intelligence/project-state",
                "/v2/intelligence/health",
                "/v2/intelligence/plan",
            ],
        }

    def agents(
        self,
        *,
        scope: str = "all",
        capability: str | None = None,
        permission: str | None = None,
        ready_only: bool = True,
    ) -> dict[str, Any]:
        normalized_scope = scope.strip().casefold() or "all"
        if normalized_scope not in {"all", "operational", "brain"}:
            raise ValueError("scope must be all, operational, or brain")

        operational: list[dict[str, Any]] = []
        brain: list[dict[str, Any]] = []
        if normalized_scope in {"all", "operational"}:
            operational = self.operational_registry.discover(
                capability=capability,
                permission=permission,
                ready_only=ready_only,
            )
        if normalized_scope in {"all", "brain"}:
            for agent_id in BRAIN_TEAM_IDS:
                item = self.runtime.registry.describe(agent_id)
                if ready_only and not item["health"]["ready"]:
                    continue
                if capability and capability.casefold() not in {
                    str(value).casefold() for value in item["capabilities"]
                }:
                    continue
                if permission and permission.casefold() not in {
                    str(value).casefold() for value in item["permissions"]
                }:
                    continue
                brain.append(item)

        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "operational_agents": operational,
            "brain_team": brain,
            "count": len(operational) + len(brain),
            "filters": {
                "scope": normalized_scope,
                "capability": capability,
                "permission": permission,
                "ready_only": ready_only,
            },
        }

    def skills(
        self,
        *,
        capability: str | None = None,
        permission: str | None = None,
        ready_only: bool = True,
    ) -> dict[str, Any]:
        if capability or permission:
            items = self.runtime.skills.discover(
                capability=capability,
                permission=permission,
                enabled_only=ready_only,
            )
        else:
            items = self.runtime.skills.list()
        if ready_only:
            items = [item for item in items if item["ready"]]
        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "skills": items,
            "count": len(items),
            "filters": {
                "capability": capability,
                "permission": permission,
                "ready_only": ready_only,
            },
        }

    def tools(
        self,
        *,
        capability: str | None = None,
        permission: str | None = None,
        ready_only: bool = True,
    ) -> dict[str, Any]:
        items = self.runtime.tools.discover(
            capability=capability,
            permission=permission,
            ready_only=ready_only,
        )
        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "tools": items,
            "count": len(items),
            "filters": {
                "capability": capability,
                "permission": permission,
                "ready_only": ready_only,
            },
            "note": "adapter_ready is runtime state; source code presence alone does not make a tool executable",
        }

    def capabilities(self) -> dict[str, Any]:
        catalog: dict[str, dict[str, set[str]]] = {}

        def ensure(capability: str) -> dict[str, set[str]]:
            return catalog.setdefault(
                str(capability),
                {
                    "operational_agents": set(),
                    "brain_agents": set(),
                    "skills": set(),
                    "ready_skills": set(),
                    "tools": set(),
                    "ready_tools": set(),
                },
            )

        for item in self.operational_registry.list():
            if not item["health"]["ready"]:
                continue
            for capability in item["capabilities"]:
                ensure(str(capability))["operational_agents"].add(str(item["agent_id"]))

        for agent_id in BRAIN_TEAM_IDS:
            item = self.runtime.registry.describe(agent_id)
            if not item["health"]["ready"]:
                continue
            for capability in item["capabilities"]:
                ensure(str(capability))["brain_agents"].add(str(item["agent_id"]))

        for item in self.runtime.skills.list():
            for capability in item["capabilities"]:
                bucket = ensure(str(capability))
                bucket["skills"].add(str(item["skill_id"]))
                if item["ready"]:
                    bucket["ready_skills"].add(str(item["skill_id"]))

        for item in self.runtime.tools.list():
            for capability in item["capabilities"]:
                bucket = ensure(str(capability))
                bucket["tools"].add(str(item["tool_id"]))
                if item["ready"]:
                    bucket["ready_tools"].add(str(item["tool_id"]))

        items: list[dict[str, Any]] = []
        for capability in sorted(catalog):
            bucket = catalog[capability]
            item = {key: sorted(value) for key, value in bucket.items()}
            executable = bool(item["ready_tools"])
            routable = bool(item["operational_agents"] or item["brain_agents"])
            skill_supported = bool(item["ready_skills"])
            items.append(
                {
                    "capability": capability,
                    **item,
                    "routable": routable,
                    "skill_supported": skill_supported,
                    "executable": executable,
                    "known": True,
                }
            )

        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "capabilities": items,
            "count": len(items),
            "semantics": {
                "known": "present in at least one canonical registry",
                "routable": "at least one ready agent declares the capability",
                "skill_supported": "at least one ready skill declares the capability",
                "executable": "at least one ready tool adapter declares the capability",
            },
        }

    def permissions(self) -> dict[str, Any]:
        catalog: dict[str, dict[str, set[str]]] = {}

        def add(permission: str, kind: str, owner_id: str) -> None:
            bucket = catalog.setdefault(
                permission,
                {"agents": set(), "brain_agents": set(), "skills": set(), "tools": set()},
            )
            bucket[kind].add(owner_id)

        for item in self.operational_registry.list():
            for permission in item["permissions"]:
                add(str(permission), "agents", str(item["agent_id"]))
        for agent_id in BRAIN_TEAM_IDS:
            item = self.runtime.registry.describe(agent_id)
            for permission in item["permissions"]:
                add(str(permission), "brain_agents", str(item["agent_id"]))
        for item in self.runtime.skills.list():
            for permission in item["permissions"]:
                add(str(permission), "skills", str(item["skill_id"]))
        for item in self.runtime.tools.list():
            for permission in item["permissions"]:
                add(str(permission), "tools", str(item["tool_id"]))

        permissions: list[dict[str, Any]] = []
        for permission in sorted(catalog):
            consumers = {key: sorted(value) for key, value in catalog[permission].items()}
            normalized = permission.casefold()
            permissions.append(
                {
                    "permission": permission,
                    "consumers": consumers,
                    "write_like": "write" in normalized or "execute" in normalized,
                    "confirmation_declared": normalized.endswith("with_confirmation"),
                    "granted_by_introspection": False,
                }
            )
        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "permissions": permissions,
            "count": len(permissions),
            "authority": "descriptive_only",
            "grants": "not_exposed_by_this_api",
        }

    def architecture(self) -> dict[str, Any]:
        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "nodes": [
                {"id": "ai_gateway", "role": "provider/model selection and credential boundary"},
                {"id": "brain_core", "role": "goal, plan, working memory, evidence"},
                {"id": "context_engine", "role": "authority-ranked context and provenance"},
                {"id": "agent_registry", "role": "operational agent discovery/readiness"},
                {"id": "brain_team", "role": "isolated Brain engineering roles"},
                {"id": "skill_registry", "role": "versioned skill contracts"},
                {"id": "tool_registry", "role": "tool metadata and adapter readiness"},
                {"id": "execution_controller", "role": "permission, approval, retry and checkpoint gate"},
                {"id": "orchestrator", "role": "durable dependency/task execution"},
                {"id": "workspace_knowledge", "role": "local-first knowledge/provenance"},
                {"id": "verification", "role": "evidence-based completion checks"},
            ],
            "edges": [
                ["ai_gateway", "brain_core", "model inference only"],
                ["agent_registry", "brain_core", "capability routing"],
                ["brain_core", "context_engine", "context assembly"],
                ["brain_core", "skill_registry", "skill discovery"],
                ["skill_registry", "tool_registry", "required capabilities"],
                ["tool_registry", "execution_controller", "adapter invocation after authorization"],
                ["execution_controller", "verification", "evidence and result"],
                ["orchestrator", "agent_registry", "delegated steps"],
                ["workspace_knowledge", "context_engine", "retrieved knowledge"],
            ],
            "invariants": [
                "provider selection does not own durable skills or memory",
                "registry metadata does not bypass execution authorization",
                "mutation requires the execution controller approval boundary",
                "introspection is read-only and grants no permissions",
                "unknown capability remains unknown instead of being guessed",
            ],
        }

    def project_state(self) -> dict[str, Any]:
        build_sha_raw = (os.getenv("RESEARCH_OS_BUILD_SHA") or "").strip()
        build_sha = build_sha_raw if _SHA_RE.fullmatch(build_sha_raw) else None
        channel_raw = (os.getenv("RESEARCH_OS_CHANNEL") or "development").strip()
        channel = channel_raw[:64] if channel_raw else "development"
        version_raw = (os.getenv("RESEARCH_OS_VERSION") or "").strip()
        version = version_raw[:64] or None
        tools = self.runtime.tools.list()
        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "build": {
                "sha": build_sha,
                "channel": channel,
                "version": version,
            },
            "storage": {
                "data_dir_configured": bool(os.getenv("RESEARCH_OS_DATA_DIR")),
                "data_dir_exposed": False,
            },
            "execution_surface": {
                "ready_tools": _unique_sorted(item["tool_id"] for item in tools if item["ready"]),
                "ready_mutating_tools": _unique_sorted(
                    item["tool_id"] for item in tools if item["ready"] and item["mutating"]
                ),
                "ready_destructive_tools": _unique_sorted(
                    item["tool_id"] for item in tools if item["ready"] and item["destructive"]
                ),
            },
            "authority": {
                "release_state_authoritative": False,
                "publication_state_authoritative": False,
                "production_state_authoritative": False,
                "reason": "runtime introspection reports local runtime state, not repository/release governance state",
            },
        }

    def health(self) -> dict[str, Any]:
        operational = self.operational_registry.readiness()
        brain_team = [self.runtime.registry.describe(agent_id) for agent_id in BRAIN_TEAM_IDS]
        skills = self.runtime.skills.list()
        tools = self.runtime.tools.list()
        brain_ready = sum(1 for item in brain_team if item["health"]["ready"])
        ready_skills = sum(1 for item in skills if item["ready"])
        ready_tools = sum(1 for item in tools if item["ready"])
        ready = bool(
            operational["ready"]
            and brain_ready >= 10
            and ready_skills > 0
            and ready_tools > 0
        )
        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "ready": ready,
            "counts": {
                "operational_agents": operational["agent_count"],
                "operational_agents_ready": operational["ready_count"],
                "brain_agents": len(brain_team),
                "brain_agents_ready": brain_ready,
                "skills": len(skills),
                "skills_ready": ready_skills,
                "tools": len(tools),
                "tools_ready": ready_tools,
                "mutating_tools_ready": sum(
                    1 for item in tools if item["ready"] and item["mutating"]
                ),
            },
            "execution_boundary": self.runtime.execution.dashboard(),
            "safety": self._safety_boundary(),
        }

    def plan(
        self,
        objective: str,
        *,
        session_id: str | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        text = objective.strip()
        if not text:
            raise ValueError("objective is required")
        if len(text) > _MAX_OBJECTIVE_CHARS:
            raise ValueError(f"objective exceeds {_MAX_OBJECTIVE_CHARS} characters")
        safe_context = dict(context or {})
        context_size = len(repr(safe_context))
        if context_size > _MAX_CONTEXT_CHARS:
            raise ValueError(f"context exceeds {_MAX_CONTEXT_CHARS} characters")
        result = self.runtime.plan(text, session_id=session_id, context=safe_context)
        plan_value = result.get("plan")
        if is_dataclass(plan_value):
            result = {**result, "plan": asdict(plan_value)}
        return {
            "contract": SYSTEM_INTROSPECTION_CONTRACT,
            "read_only": True,
            "execution_performed": False,
            "result": sanitize_external(result),
        }

    @staticmethod
    def _safety_boundary() -> dict[str, Any]:
        return {
            "introspection_grants_permissions": False,
            "plan_executes_tools": False,
            "direct_adapter_access": False,
            "secret_values_returned": False,
            "hidden_chain_of_thought_exposed": False,
            "mutation_requires_execution_controller": True,
            "production_release_bypass": False,
        }


def parse_ready_only(value: str | None) -> bool:
    return _bool_query(value, default=True)
