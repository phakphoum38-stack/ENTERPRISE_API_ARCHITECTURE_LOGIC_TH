from __future__ import annotations

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


@dataclass(frozen=True)
class AgentTask:
    task_id: str
    objective: str
    requested_agent: str | None = None
    context: dict[str, Any] | None = None


AGENTS: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        "research",
        "Research Agent",
        "Research, synthesis, evidence review and knowledge creation.",
        ("research", "summarize", "synthesize", "memory_search", "knowledge_create"),
        ("memory.read", "knowledge.read", "knowledge.write"),
        "shared:research",
    ),
    AgentDefinition(
        "document",
        "Document Agent",
        "Document extraction, classification and structured analysis.",
        ("document_read", "pdf", "word", "excel", "powerpoint", "markdown", "classify"),
        ("documents.read", "memory.read", "knowledge.write"),
        "shared:documents",
    ),
    AgentDefinition(
        "github",
        "GitHub Agent",
        "Repository, commit, PR, issue and workflow intelligence.",
        ("github", "repository", "commit", "pull_request", "issue", "workflow", "release"),
        ("github.read", "memory.read"),
        "shared:github",
    ),
    AgentDefinition(
        "google_workspace",
        "Google Workspace Agent",
        "Drive, Docs, Sheets, Calendar, Gmail and Workspace coordination.",
        ("drive", "docs", "sheets", "calendar", "gmail", "contacts", "tasks", "meet", "forms", "chat"),
        ("google.read", "google.write.with_confirmation", "memory.read"),
        "shared:google-workspace",
    ),
    AgentDefinition(
        "shift",
        "Shift Agent",
        "Roster reading, assignment analysis, substitution, leave and conflict detection.",
        ("shift", "roster", "schedule", "replacement", "leave", "absence", "conflict", "calendar_sync"),
        ("documents.read", "google.sheets.read", "calendar.write.with_confirmation", "memory.read"),
        "shared:shift",
    ),
)


class AgentRegistry:
    def __init__(self, agents: Iterable[AgentDefinition] = AGENTS) -> None:
        self._agents = {agent.agent_id: agent for agent in agents}

    def list(self) -> list[dict[str, Any]]:
        return [asdict(agent) for agent in self._agents.values()]

    def get(self, agent_id: str) -> AgentDefinition:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise ValueError(f"unknown agent: {agent_id}") from exc

    def enabled(self) -> list[AgentDefinition]:
        return [agent for agent in self._agents.values() if agent.enabled]


class AgentRouter:
    def __init__(self, registry: AgentRegistry | None = None) -> None:
        self.registry = registry or AgentRegistry()

    def route(self, objective: str, requested_agent: str | None = None) -> dict[str, Any]:
        text = objective.strip().lower()
        if not text:
            raise ValueError("objective is required")

        if requested_agent:
            selected = self.registry.get(requested_agent)
            if not selected.enabled:
                raise ValueError(f"agent disabled: {requested_agent}")
            return self._result(selected, "explicit")

        best: AgentDefinition | None = None
        best_score = 0
        for agent in self.registry.enabled():
            score = sum(2 if token in text else 0 for token in agent.capabilities)
            score += sum(1 for token in agent.name.lower().split() if token in text)
            if score > best_score:
                best = agent
                best_score = score

        if best is None:
            best = self.registry.get("research")
            return self._result(best, "default")
        return self._result(best, "capability_match", score=best_score)

    @staticmethod
    def _result(agent: AgentDefinition, reason: str, score: int = 0) -> dict[str, Any]:
        return {
            "agent": asdict(agent),
            "reason": reason,
            "score": score,
            "execution_mode": "plan_only",
            "requires_confirmation_for_writes": any(
                permission.endswith("with_confirmation") for permission in agent.permissions
            ),
        }


def platform_dashboard() -> dict[str, Any]:
    registry = AgentRegistry()
    agents = registry.list()
    return {
        "platform": "research_os_agents",
        "version": "1.0-foundation",
        "agent_count": len(agents),
        "agents": agents,
        "router": "capability-based",
        "task_contract": ["task_id", "objective", "requested_agent", "context"],
        "shared_context": "interface-ready",
        "shared_memory": "interface-ready",
        "event_bus": "planned",
        "task_queue": "planned",
        "write_policy": "explicit_confirmation",
    }
