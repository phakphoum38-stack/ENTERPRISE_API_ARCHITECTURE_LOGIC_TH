from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SkillOrigin(str, Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    origin: SkillOrigin
    capability: str
    description: str
    native_v3: bool = True


class UnifiedSkillRegistry:
    """Native V3 registry for skills migrated from V1, V2, and V3.

    Runtime dependencies never call V1/V2 APIs directly. Older knowledge is
    represented as V3-native skill metadata with explicit provenance.
    """

    def __init__(self, skills: tuple[SkillDefinition, ...] | None = None) -> None:
        self._skills = skills or self.default_skills()
        self._by_name = {skill.name: skill for skill in self._skills}

    @staticmethod
    def default_skills() -> tuple[SkillDefinition, ...]:
        return (
            SkillDefinition("memory-retrieval", SkillOrigin.V1, "memory", "Retrieve durable local knowledge."),
            SkillDefinition("conversation-analysis", SkillOrigin.V1, "analysis", "Analyze conversations without mutating source data."),
            SkillDefinition("provider-routing", SkillOrigin.V1, "providers", "Select a ready AI provider without exposing credentials."),
            SkillDefinition("agent-routing", SkillOrigin.V2, "orchestration", "Route work to capability-matched agents."),
            SkillDefinition("durable-orchestration", SkillOrigin.V2, "orchestration", "Persist, resume, retry, and cancel orchestration runs."),
            SkillDefinition("workspace-knowledge", SkillOrigin.V2, "knowledge", "Search workspace knowledge with provenance."),
            SkillDefinition("developer-access", SkillOrigin.V2, "security", "Enforce owner-controlled developer access and trial isolation."),
            SkillDefinition("adaptive-hierarchy", SkillOrigin.V3, "scaling", "Select the smallest safe 3^1-to-6^6 logical hierarchy."),
            SkillDefinition("factory-execution", SkillOrigin.V3, "execution", "Execute deterministic factory stages with evidence."),
            SkillDefinition("provider-resilience", SkillOrigin.V3, "resilience", "Apply retry, circuit-breaker, and provider failover policy."),
            SkillDefinition("user-isolation", SkillOrigin.V3, "security", "Keep user/profile data and service context isolated."),
        )

    def list(self) -> tuple[SkillDefinition, ...]:
        return self._skills

    def get(self, name: str) -> SkillDefinition | None:
        return self._by_name.get(name)

    def by_origin(self, origin: SkillOrigin) -> tuple[SkillDefinition, ...]:
        return tuple(skill for skill in self._skills if skill.origin is origin)

    def by_capability(self, capability: str) -> tuple[SkillDefinition, ...]:
        wanted = capability.strip().lower()
        return tuple(
            skill for skill in self._skills if skill.capability.lower() == wanted
        )

    def origins(self) -> tuple[SkillOrigin, ...]:
        return tuple(origin for origin in SkillOrigin if self.by_origin(origin))
