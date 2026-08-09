from __future__ import annotations

import threading
import time
from dataclasses import asdict, dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    name: str
    description: str
    capabilities: tuple[str, ...]
    permissions: tuple[str, ...]
    memory_scope: str
    enabled: bool = True
    provider_preferences: tuple[str, ...] = ("local", "openai-compatible", "gemini", "anthropic")
    model_preferences: tuple[str, ...] = ()
    fallback_agents: tuple[str, ...] = ("research",)
    permission_profile: str = "standard"


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    objective: str
    requested_agent: str | None = None
    context: dict[str, Any] | None = None


@dataclass
class AgentHealth:
    agent_id: str
    status: str
    ready: bool
    reason: str | None = None
    checked_at: float = 0.0


_HEALTH_STATES = {"ready", "degraded", "unavailable", "disabled"}
_PERMISSION_PROFILES = {"read_only", "standard", "write_confirmed", "network_sensitive"}


AGENTS: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        "research",
        "Research Agent",
        "Research, synthesis, evidence review and knowledge creation.",
        ("research", "summarize", "synthesize", "memory_search", "knowledge_create"),
        ("memory.read", "knowledge.read", "knowledge.write"),
        "shared:research",
        provider_preferences=("local", "openai-compatible", "gemini", "anthropic"),
        model_preferences=("general", "reasoning"),
        fallback_agents=(),
        permission_profile="standard",
    ),
    AgentDefinition(
        "developer",
        "Developer Agent",
        "Code, API, architecture, testing, build and debugging assistance.",
        ("code", "coding", "developer", "api", "architecture", "test", "build", "debug", "ci", "release"),
        ("source.read", "source.write.with_confirmation", "runtime.read", "memory.read"),
        "shared:developer",
        provider_preferences=("openai-compatible", "local", "gemini", "anthropic"),
        model_preferences=("coding", "reasoning"),
        fallback_agents=("research",),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "document",
        "Document Agent",
        "Document extraction, classification and structured analysis.",
        ("document_read", "pdf", "word", "excel", "powerpoint", "markdown", "classify"),
        ("documents.read", "memory.read", "knowledge.write"),
        "shared:documents",
        provider_preferences=("local", "openai-compatible", "gemini"),
        model_preferences=("document", "general"),
        fallback_agents=("research",),
        permission_profile="standard",
    ),
    AgentDefinition(
        "github",
        "GitHub Agent",
        "Repository, commit, PR, issue and workflow intelligence.",
        ("github", "repository", "commit", "pull_request", "issue", "workflow", "release"),
        ("github.read", "memory.read"),
        "shared:github",
        provider_preferences=("local", "openai-compatible", "gemini"),
        model_preferences=("coding", "general"),
        fallback_agents=("developer", "research"),
        permission_profile="network_sensitive",
    ),
    AgentDefinition(
        "google_workspace",
        "Google Workspace Agent",
        "Drive, Docs, Sheets, Calendar, Gmail and Workspace coordination.",
        ("drive", "docs", "sheets", "calendar", "gmail", "contacts", "tasks", "meet", "forms", "chat"),
        ("google.read", "google.write.with_confirmation", "memory.read"),
        "shared:google-workspace",
        provider_preferences=("gemini", "openai-compatible", "local"),
        model_preferences=("general",),
        fallback_agents=("document", "research"),
        permission_profile="network_sensitive",
    ),
    AgentDefinition(
        "shift",
        "Shift Agent",
        "Roster reading, assignment analysis, substitution, leave and conflict detection.",
        ("shift", "roster", "schedule", "replacement", "leave", "absence", "conflict", "calendar_sync"),
        ("documents.read", "google.sheets.read", "calendar.write.with_confirmation", "memory.read"),
        "shared:shift",
        provider_preferences=("local", "gemini", "openai-compatible"),
        model_preferences=("general", "reasoning"),
        fallback_agents=("google_workspace", "document", "research"),
        permission_profile="write_confirmed",
    ),
)


class AgentRegistry:
    """Runtime agent registry with capability discovery and readiness state."""

    def __init__(self, agents: Iterable[AgentDefinition] = AGENTS) -> None:
        self._lock = threading.RLock()
        self._agents: dict[str, AgentDefinition] = {}
        self._health: dict[str, AgentHealth] = {}
        for agent in agents:
            self.register(agent)

    @staticmethod
    def _validate(agent: AgentDefinition) -> None:
        if not agent.agent_id.strip():
            raise ValueError("agent_id is required")
        if not agent.name.strip():
            raise ValueError("agent name is required")
        if not agent.capabilities:
            raise ValueError(f"agent capabilities are required: {agent.agent_id}")
        if agent.permission_profile not in _PERMISSION_PROFILES:
            raise ValueError(f"invalid permission profile: {agent.permission_profile}")

    def register(self, agent: AgentDefinition, *, replace: bool = False) -> dict[str, Any]:
        self._validate(agent)
        with self._lock:
            if agent.agent_id in self._agents and not replace:
                raise ValueError(f"agent already registered: {agent.agent_id}")
            self._agents[agent.agent_id] = agent
            status = "ready" if agent.enabled else "disabled"
            self._health[agent.agent_id] = AgentHealth(
                agent_id=agent.agent_id,
                status=status,
                ready=agent.enabled,
                checked_at=time.time(),
            )
            return self.describe(agent.agent_id)

    def unregister(self, agent_id: str) -> dict[str, Any]:
        with self._lock:
            agent = self.get(agent_id)
            self._agents.pop(agent_id, None)
            self._health.pop(agent_id, None)
            return asdict(agent)

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self.describe(agent_id) for agent_id in self._agents]

    def get(self, agent_id: str) -> AgentDefinition:
        with self._lock:
            try:
                return self._agents[agent_id]
            except KeyError as exc:
                raise ValueError(f"unknown agent: {agent_id}") from exc

    def enabled(self) -> list[AgentDefinition]:
        with self._lock:
            return [agent for agent in self._agents.values() if agent.enabled]

    def ready(self) -> list[AgentDefinition]:
        with self._lock:
            return [agent for agent in self._agents.values() if agent.enabled and self._health[agent.agent_id].ready]

    def set_health(self, agent_id: str, status: str, *, reason: str | None = None) -> dict[str, Any]:
        normalized = status.strip().lower()
        if normalized not in _HEALTH_STATES:
            raise ValueError(f"invalid agent health state: {status}")
        with self._lock:
            agent = self.get(agent_id)
            if not agent.enabled:
                normalized = "disabled"
            health = AgentHealth(
                agent_id=agent_id,
                status=normalized,
                ready=normalized in {"ready", "degraded"} and agent.enabled,
                reason=reason,
                checked_at=time.time(),
            )
            self._health[agent_id] = health
            return asdict(health)

    def health(self, agent_id: str) -> dict[str, Any]:
        with self._lock:
            self.get(agent_id)
            return asdict(self._health[agent_id])

    def describe(self, agent_id: str) -> dict[str, Any]:
        with self._lock:
            agent = self.get(agent_id)
            return {**asdict(agent), "health": asdict(self._health[agent_id])}

    def discover(self, *, capability: str | None = None, permission: str | None = None, ready_only: bool = True) -> list[dict[str, Any]]:
        normalized_capability = capability.strip().casefold() if capability else None
        normalized_permission = permission.strip().casefold() if permission else None
        with self._lock:
            matches: list[dict[str, Any]] = []
            for agent in self._agents.values():
                health = self._health[agent.agent_id]
                if ready_only and not health.ready:
                    continue
                if normalized_capability and normalized_capability not in {item.casefold() for item in agent.capabilities}:
                    continue
                if normalized_permission and normalized_permission not in {item.casefold() for item in agent.permissions}:
                    continue
                matches.append(self.describe(agent.agent_id))
            return matches

    def readiness(self) -> dict[str, Any]:
        agents = self.list()
        ready_count = sum(1 for agent in agents if agent["health"]["ready"])
        unavailable_count = sum(1 for agent in agents if agent["health"]["status"] == "unavailable")
        return {
            "agent_count": len(agents),
            "ready_count": ready_count,
            "unavailable_count": unavailable_count,
            "ready": ready_count > 0,
            "agents": agents,
        }


class AgentRouter:
    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self.registry = registry or AgentRegistry()

    def route(
        self,
        objective: str,
        requested_agent: str | None = None,
        *,
        available_providers: Iterable[str] | None = None,
        allow_fallback: bool = True,
    ) -> dict[str, Any]:
        text = objective.strip().lower()
        if not text:
            raise ValueError("objective is required")
        providers = {item.strip().casefold() for item in available_providers or () if item.strip()}

        if requested_agent:
            selected = self.registry.get(requested_agent)
            if not selected.enabled:
                raise ValueError(f"agent disabled: {requested_agent}")
            health = self.registry.health(requested_agent)
            if health["ready"]:
                return self._result(selected, "explicit", health=health, providers=providers)
            if allow_fallback:
                fallback = self._fallback(selected)
                if fallback is not None:
                    return self._result(
                        fallback,
                        "explicit_fallback",
                        health=self.registry.health(fallback.agent_id),
                        providers=providers,
                        fallback_from=selected.agent_id,
                    )
            raise ValueError(f"agent unavailable: {requested_agent}")

        best: AgentDefinition | None = None
        best_score = 0
        for agent in self.registry.ready():
            score = sum(2 if token in text else 0 for token in agent.capabilities)
            score += sum(1 for token in agent.name.lower().split() if token in text)
            if score > best_score:
                best = agent
                best_score = score

        if best is None:
            try:
                research = self.registry.get("research")
                health = self.registry.health("research")
                if health["ready"]:
                    return self._result(research, "default", health=health, providers=providers)
            except ValueError:
                pass
            ready_agents = self.registry.ready()
            if not ready_agents:
                raise ValueError("no ready agents available")
            best = ready_agents[0]
            return self._result(best, "fallback_ready_agent", health=self.registry.health(best.agent_id), providers=providers)

        return self._result(best, "capability_match", score=best_score, health=self.registry.health(best.agent_id), providers=providers)

    def _fallback(self, agent: AgentDefinition) -> AgentDefinition | None:
        for candidate_id in agent.fallback_agents:
            try:
                candidate = self.registry.get(candidate_id)
                if candidate.enabled and self.registry.health(candidate_id)["ready"]:
                    return candidate
            except ValueError:
                continue
        return None

    @staticmethod
    def _permission_summary(agent: AgentDefinition) -> dict[str, Any]:
        writes = [permission for permission in agent.permissions if "write" in permission]
        network = agent.permission_profile == "network_sensitive" or any(
            permission.startswith(("github.", "google.", "calendar.")) for permission in agent.permissions
        )
        return {
            "profile": agent.permission_profile,
            "write_capable": bool(writes),
            "requires_confirmation": any(permission.endswith("with_confirmation") for permission in agent.permissions),
            "network_sensitive": network,
        }

    @staticmethod
    def _select_provider(agent: AgentDefinition, providers: set[str]) -> dict[str, Any]:
        if not providers:
            return {
                "provider": None,
                "model_preferences": list(agent.model_preferences),
                "reason": "runtime_provider_selection",
            }
        for provider in agent.provider_preferences:
            if provider.casefold() in providers:
                return {
                    "provider": provider,
                    "model_preferences": list(agent.model_preferences),
                    "reason": "agent_preference",
                }
        return {
            "provider": None,
            "model_preferences": list(agent.model_preferences),
            "reason": "no_preferred_provider_ready",
        }

    @classmethod
    def _result(
        cls,
        agent: AgentDefinition,
        reason: str,
        score: int = 0,
        health: dict[str, Any] | None = None,
        providers: set[str] | None = None,
        fallback_from: str | None = None,
    ) -> dict[str, Any]:
        permission = cls._permission_summary(agent)
        return {
            "agent": asdict(agent),
            "health": health or {},
            "reason": reason,
            "score": score,
            "fallback_from": fallback_from,
            "execution_mode": "runtime_dispatch",
            "provider_selection": cls._select_provider(agent, providers or set()),
            "permission": permission,
            "requires_confirmation_for_writes": permission["requires_confirmation"],
        }


REGISTRY = AgentRegistry()
ROUTER = AgentRouter(REGISTRY)


def platform_dashboard(registry: AgentRegistry | None = None) -> dict[str, Any]:
    registry = registry or REGISTRY
    readiness = registry.readiness()
    return {
        "platform": "research_os_agents",
        "version": "2.0-dynamic-registry",
        "agent_count": readiness["agent_count"],
        "ready_agent_count": readiness["ready_count"],
        "agents": readiness["agents"],
        "router": "capability-readiness-provider-fallback",
        "task_contract": ["task_id", "objective", "requested_agent", "context"],
        "shared_context": "local-persistent",
        "shared_memory": "scope-ready",
        "event_bus": "active",
        "task_queue": "active",
        "write_policy": "explicit_confirmation",
        "dynamic_registration": "active",
        "capability_discovery": "active",
        "health_readiness": "active",
        "provider_preferences": "per-agent",
        "fallback_routing": "active",
        "permission_profiles": "active",
    }
