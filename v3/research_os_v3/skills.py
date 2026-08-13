from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SkillOrigin(str, Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"
    OWNER_FRIEND = "owner-friend"
    LEGACY = "legacy"


@dataclass(frozen=True)
class SkillDefinition:
    name: str
    origin: SkillOrigin
    capability: str
    description: str
    native_v3: bool = True
    runtime_mode: str = "native"
    source: str = "v3"

    def __post_init__(self) -> None:
        # Runtime mode is the source of truth: context adapters are represented
        # in V3, but they are not executable V3-native implementations.
        if self.runtime_mode != "native" and self.native_v3:
            object.__setattr__(self, "native_v3", False)


class UnifiedSkillRegistry:
    """Single V3 registry for native, migrated, Owner/Friend, and legacy skills.

    V3 remains the only orchestration authority. Older capability lines are
    represented through explicit V3 metadata/context adapters; they are never
    started as competing orchestrators. Runtime mode makes that distinction
    visible instead of pretending every migrated capability is executable.
    """

    def __init__(self, skills: tuple[SkillDefinition, ...] | None = None) -> None:
        self._skills = skills or self.default_skills()
        names = [skill.name for skill in self._skills]
        if len(names) != len(set(names)):
            duplicates = sorted({name for name in names if names.count(name) > 1})
            raise ValueError(f"duplicate skills: {', '.join(duplicates)}")
        self._by_name = {skill.name: skill for skill in self._skills}

    @staticmethod
    def default_skills() -> tuple[SkillDefinition, ...]:
        migrated = "context-adapter"
        owner_source = "owner_special/research_os_friend/catalog.py"
        legacy_source = "tools"
        return (
            # V1/V2/V3 capability line already migrated into the V3 contract.
            SkillDefinition("memory-retrieval", SkillOrigin.V1, "memory", "Retrieve durable local knowledge.", runtime_mode=migrated, source="tools/research_os_api"),
            SkillDefinition("memory-persistence", SkillOrigin.V3, "memory", "Persist explicit user-scoped durable memory."),
            SkillDefinition("conversation-analysis", SkillOrigin.V1, "analysis", "Analyze conversations without mutating source data.", runtime_mode=migrated, source="tools/research_os_api"),
            SkillDefinition("chat-runtime", SkillOrigin.V3, "chat", "Execute provider-backed conversations with optional local memory context."),
            SkillDefinition("provider-routing", SkillOrigin.V1, "providers", "Select a ready AI provider without exposing credentials.", runtime_mode=migrated, source="tools/research_os_api/providers.py"),
            SkillDefinition("agent-routing", SkillOrigin.V2, "orchestration", "Route work to capability-matched agents.", runtime_mode=migrated, source="tools/research_os_api/agent_orchestrator.py"),
            SkillDefinition("agent-execution", SkillOrigin.V3, "agents", "Run bounded role-based V3 agents on demand."),
            SkillDefinition("durable-orchestration", SkillOrigin.V2, "orchestration", "Persist, resume, retry, and cancel orchestration runs.", runtime_mode=migrated, source="tools/research_os_api/agent_orchestrator.py"),
            SkillDefinition("workspace-knowledge", SkillOrigin.V2, "knowledge", "Search workspace knowledge with provenance.", runtime_mode=migrated, source="tools/research_os_api"),
            SkillDefinition("developer-access", SkillOrigin.V2, "security", "Enforce owner-controlled developer access and trial isolation.", runtime_mode=migrated, source="tools/research_os_api/developer_access.py"),
            SkillDefinition("adaptive-hierarchy", SkillOrigin.V3, "scaling", "Select the smallest safe 3^1-to-10^10 logical hierarchy."),
            SkillDefinition("factory-execution", SkillOrigin.V3, "execution", "Execute deterministic factory stages with evidence."),
            SkillDefinition("governed-tool-execution", SkillOrigin.V3, "tools", "Resolve tools through explicit risk and approval policy."),
            SkillDefinition("provider-resilience", SkillOrigin.V3, "resilience", "Apply retry, circuit-breaker, and provider failover policy."),
            SkillDefinition("user-isolation", SkillOrigin.V3, "security", "Keep user/profile data and service context isolated."),

            # Owner/Friend built-ins are migrated as V3 context adapters. These
            # names match the preserved catalog exactly so no owner skill is lost.
            SkillDefinition("analysis", SkillOrigin.OWNER_FRIEND, "reasoning", "Analyze goals, constraints, and evidence.", runtime_mode=migrated, source=owner_source),
            SkillDefinition("planning", SkillOrigin.OWNER_FRIEND, "orchestration", "Turn a goal into reviewable execution steps.", runtime_mode=migrated, source=owner_source),
            SkillDefinition("coding", SkillOrigin.OWNER_FRIEND, "engineering", "Design, implement, test, and review software changes.", runtime_mode=migrated, source=owner_source),
            SkillDefinition("research", SkillOrigin.OWNER_FRIEND, "knowledge", "Gather and compare source-backed information.", runtime_mode=migrated, source=owner_source),
            SkillDefinition("data", SkillOrigin.OWNER_FRIEND, "analytics", "Inspect structured data and produce quantitative findings.", runtime_mode=migrated, source=owner_source),
            SkillDefinition("documents", SkillOrigin.OWNER_FRIEND, "artifacts", "Create and transform durable written artifacts.", runtime_mode=migrated, source=owner_source),
            SkillDefinition("automation", SkillOrigin.OWNER_FRIEND, "operations", "Define repeatable scheduled or triggered workflows.", runtime_mode=migrated, source=owner_source),
            SkillDefinition("memory", SkillOrigin.OWNER_FRIEND, "context", "Use owner-scoped context without cross-profile leakage.", runtime_mode=migrated, source=owner_source),
            SkillDefinition("security", SkillOrigin.OWNER_FRIEND, "assurance", "Apply permission, secret, and isolation boundaries.", runtime_mode=migrated, source=owner_source),
            SkillDefinition("quality", SkillOrigin.OWNER_FRIEND, "assurance", "Validate outputs with tests and evidence.", runtime_mode=migrated, source=owner_source),

            # Preserved legacy engines are exposed through the same registry so
            # chat/agents can reason about them without starting another master.
            SkillDefinition("research-curation", SkillOrigin.LEGACY, "knowledge", "Curate research artifacts with provenance and quality checks.", runtime_mode=migrated, source=f"{legacy_source}/research_curator"),
            SkillDefinition("knowledge-graph", SkillOrigin.LEGACY, "knowledge", "Build and inspect linked workspace knowledge relationships.", runtime_mode=migrated, source=f"{legacy_source}/research_curator"),
            SkillDefinition("house-command-dispatch", SkillOrigin.LEGACY, "operations", "Dispatch governed house commands through the preserved command boundary.", runtime_mode=migrated, source=f"{legacy_source}/house_command"),
            SkillDefinition("github-integration", SkillOrigin.LEGACY, "integration", "Inspect repository and delivery context through governed GitHub integration.", runtime_mode=migrated, source=f"{legacy_source}/research_os_api"),
            SkillDefinition("google-workspace-integration", SkillOrigin.LEGACY, "integration", "Work with Google Workspace through owner-authorized integration boundaries.", runtime_mode=migrated, source=f"{legacy_source}/research_os_api"),
            SkillDefinition("cloud-conversation-sync", SkillOrigin.LEGACY, "memory", "Synchronize conversation records without replacing local ownership rules.", runtime_mode=migrated, source=f"{legacy_source}/research_os_api"),
            SkillDefinition("orchestration-observability", SkillOrigin.LEGACY, "quality", "Inspect orchestration status, evidence, and operational signals.", runtime_mode=migrated, source=f"{legacy_source}/research_os_api"),
            SkillDefinition("completion-crew", SkillOrigin.LEGACY, "orchestration", "Coordinate completion checks for bounded delivery work.", runtime_mode=migrated, source=f"{legacy_source}/research_os_api"),
            SkillDefinition("quality-gate", SkillOrigin.LEGACY, "quality", "Run release-readiness and contract validation gates.", runtime_mode=migrated, source=f"{legacy_source}/research_os_api"),
            SkillDefinition("file-audit-6x6", SkillOrigin.LEGACY, "quality", "Audit candidate repository files using adaptive 6^6 evidence rules.", runtime_mode=migrated, source=f"{legacy_source}/file_audit_v6x6.py"),
            SkillDefinition("developer-identity", SkillOrigin.LEGACY, "security", "Verify short-lived trusted developer identity assertions.", runtime_mode=migrated, source=f"{legacy_source}/research_os_api/developer_identity.py"),
            SkillDefinition("provider-readiness", SkillOrigin.LEGACY, "providers", "Inspect provider readiness without exposing credentials.", runtime_mode=migrated, source=f"{legacy_source}/research_os_api/provider_readiness.py"),
            SkillDefinition("owner-policy", SkillOrigin.LEGACY, "security", "Apply owner-managed permission and approval policy.", runtime_mode=migrated, source="owner_special/research_os_friend/policy.py"),
            SkillDefinition("evidence-recording", SkillOrigin.LEGACY, "quality", "Record credential-redacted execution evidence and audit events.", runtime_mode=migrated, source="owner_special/research_os_friend/evidence.py"),
            SkillDefinition("v3-bridge", SkillOrigin.LEGACY, "integration", "Bridge preserved Owner/Friend capabilities into V3 contracts without a second master.", runtime_mode=migrated, source="owner_special/research_os_friend/v3_bridge.py"),
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

    def conversation_context(self) -> str:
        """Return a secret-free capability catalog for provider/agent routing context."""
        lines = [
            "Unified Research OS skills (V3 is the single execution authority):"
        ]
        for skill in self._skills:
            lines.append(
                f"- {skill.name} [{skill.origin.value}/{skill.capability}; {skill.runtime_mode}]: "
                f"{skill.description}"
            )
        lines.append(
            "Context-adapter skills describe preserved capability knowledge; do not claim "
            "they executed unless a V3 tool/agent/runtime result proves execution."
        )
        return "\n".join(lines)
