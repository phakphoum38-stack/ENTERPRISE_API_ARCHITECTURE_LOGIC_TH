from __future__ import annotations

from dataclasses import dataclass

from .providers import CompletionRequest, CompletionResponse, ProviderRegistry
from .skills import UnifiedSkillRegistry
from .tools import UnifiedToolRegistry


@dataclass(frozen=True)
class AgentDefinition:
    name: str
    role: str
    description: str
    skills: tuple[str, ...]
    tools: tuple[str, ...] = ()


class UnifiedAgentRegistry:
    """V3-native agent catalog. Agents are roles, not permanently running workers."""

    def __init__(
        self,
        *,
        skills: UnifiedSkillRegistry,
        tools: UnifiedToolRegistry,
    ) -> None:
        self.skills = skills
        self.tools = tools
        self._agents = {agent.name: agent for agent in self.default_agents()}
        self._validate()

    @staticmethod
    def default_agents() -> tuple[AgentDefinition, ...]:
        return (
            AgentDefinition(
                "researcher",
                "research",
                "Synthesizes evidence and workspace knowledge.",
                ("memory-retrieval", "workspace-knowledge", "conversation-analysis"),
                ("capacity-inspect",),
            ),
            AgentDefinition(
                "architect",
                "architecture",
                "Designs system structure and orchestration plans.",
                ("adaptive-hierarchy", "durable-orchestration", "factory-execution"),
                ("capacity-inspect",),
            ),
            AgentDefinition(
                "builder",
                "implementation",
                "Produces implementation guidance under governed execution.",
                ("factory-execution", "provider-routing"),
                ("echo",),
            ),
            AgentDefinition(
                "reviewer",
                "quality",
                "Reviews work for correctness, risk, and evidence quality.",
                ("conversation-analysis", "provider-resilience", "user-isolation"),
                (),
            ),
            AgentDefinition(
                "release-guardian",
                "release",
                "Checks release readiness and evidence boundaries.",
                ("factory-execution", "developer-access", "user-isolation"),
                (),
            ),
        )

    def _validate(self) -> None:
        for agent in self._agents.values():
            missing_skills = [name for name in agent.skills if self.skills.get(name) is None]
            missing_tools = [name for name in agent.tools if self.tools.get(name) is None]
            if missing_skills or missing_tools:
                raise ValueError(
                    f"agent {agent.name} references missing capabilities: "
                    f"skills={missing_skills}, tools={missing_tools}"
                )

    def list(self) -> tuple[AgentDefinition, ...]:
        return tuple(self._agents[name] for name in sorted(self._agents))

    def get(self, name: str) -> AgentDefinition | None:
        return self._agents.get(name)

    def run(
        self,
        name: str,
        prompt: str,
        *,
        providers: ProviderRegistry,
        preferred_provider: str | None = None,
        context_text: str | None = None,
    ) -> CompletionResponse:
        agent = self._agents.get(name)
        if agent is None:
            raise KeyError(name)
        system_prompt = (
            f"You are the Research OS V3 agent '{agent.name}' with role '{agent.role}'. "
            f"Use only the capabilities assigned to this agent. Skills: {', '.join(agent.skills)}. "
            f"Tools available by policy: {', '.join(agent.tools) if agent.tools else 'none'}. "
            "Be concise, evidence-aware, and do not claim actions that were not executed."
        )
        if context_text:
            system_prompt += f"\n\nRelevant local memory/context:\n{context_text}"
        return providers.complete(
            CompletionRequest(prompt=prompt, system_prompt=system_prompt),
            preferred=preferred_provider,
        )
