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
    execution_adapter: str = "v3-core"

    def __post_init__(self) -> None:
        if self.runtime_mode not in {"native", "context-adapter"}:
            raise ValueError(f"unsupported runtime_mode: {self.runtime_mode}")
        if self.runtime_mode != "native" and self.native_v3:
            object.__setattr__(self, "native_v3", False)


class UnifiedSkillRegistry:
    """One V3 registry for core and migrated capabilities.

    Migrated V1/V2, Owner/Friend and legacy lines are exposed as V3-native
    adapters. The adapters preserve the old capability semantics without
    starting a second orchestrator. ``UnifiedMasterOrchestrator`` remains the
    only coordination authority.
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
        adapter = "v3-adapter"
        owner_source = "owner_special/research_os_friend/catalog.py"
        legacy_source = "tools"
        return (
            SkillDefinition("memory-retrieval", SkillOrigin.V1, "memory", "Retrieve durable local knowledge.", source="tools/research_os_api/memory.py", execution_adapter=adapter),
            SkillDefinition("memory-persistence", SkillOrigin.V3, "memory", "Persist explicit user-scoped durable memory."),
            SkillDefinition("conversation-analysis", SkillOrigin.V1, "analysis", "Analyze conversations without mutating source data.", source="tools/research_os_api", execution_adapter=adapter),
            SkillDefinition("chat-runtime", SkillOrigin.V3, "chat", "Execute provider-backed conversations with optional local memory context."),
            SkillDefinition("provider-routing", SkillOrigin.V1, "providers", "Select a ready AI provider without exposing credentials.", source="tools/research_os_api/providers.py", execution_adapter=adapter),
            SkillDefinition("agent-routing", SkillOrigin.V2, "orchestration", "Route work to capability-matched agents.", source="tools/research_os_api/agent_orchestrator.py", execution_adapter=adapter),
            SkillDefinition("agent-execution", SkillOrigin.V3, "agents", "Run bounded role-based V3 agents on demand."),
            SkillDefinition("durable-orchestration", SkillOrigin.V2, "orchestration", "Persist, resume, retry, and cancel orchestration runs.", source="tools/research_os_api/agent_orchestrator.py", execution_adapter=adapter),
            SkillDefinition("workspace-knowledge", SkillOrigin.V2, "knowledge", "Search workspace knowledge with provenance.", source="tools/research_os_api", execution_adapter=adapter),
            SkillDefinition("developer-access", SkillOrigin.V2, "security", "Enforce owner-controlled developer access and trial isolation.", source="tools/research_os_api/developer_access.py", execution_adapter=adapter),
            SkillDefinition("adaptive-hierarchy", SkillOrigin.V3, "scaling", "Select the smallest safe 3^1-to-10^10 logical hierarchy."),
            SkillDefinition("factory-execution", SkillOrigin.V3, "execution", "Execute deterministic factory stages with evidence."),
            SkillDefinition("governed-tool-execution", SkillOrigin.V3, "tools", "Resolve tools through explicit risk and approval policy."),
            SkillDefinition("provider-resilience", SkillOrigin.V3, "resilience", "Apply retry, circuit-breaker, and provider failover policy."),
            SkillDefinition("user-isolation", SkillOrigin.V3, "security", "Keep user/profile data and service context isolated."),

            SkillDefinition("analysis", SkillOrigin.OWNER_FRIEND, "reasoning", "Analyze goals, constraints, and evidence.", source=owner_source, execution_adapter=adapter),
            SkillDefinition("planning", SkillOrigin.OWNER_FRIEND, "orchestration", "Turn a goal into reviewable execution steps.", source=owner_source, execution_adapter=adapter),
            SkillDefinition("coding", SkillOrigin.OWNER_FRIEND, "engineering", "Design, implement, test, and review software changes.", source=owner_source, execution_adapter=adapter),
            SkillDefinition("research", SkillOrigin.OWNER_FRIEND, "knowledge", "Gather and compare source-backed information.", source=owner_source, execution_adapter=adapter),
            SkillDefinition("data", SkillOrigin.OWNER_FRIEND, "analytics", "Inspect structured data and produce quantitative findings.", source=owner_source, execution_adapter=adapter),
            SkillDefinition("documents", SkillOrigin.OWNER_FRIEND, "artifacts", "Create and transform durable written artifacts.", source=owner_source, execution_adapter=adapter),
            SkillDefinition("automation", SkillOrigin.OWNER_FRIEND, "operations", "Define repeatable scheduled or triggered workflows.", source=owner_source, execution_adapter=adapter),
            SkillDefinition("memory", SkillOrigin.OWNER_FRIEND, "context", "Use owner-scoped context without cross-profile leakage.", source=owner_source, execution_adapter=adapter),
            SkillDefinition("security", SkillOrigin.OWNER_FRIEND, "assurance", "Apply permission, secret, and isolation boundaries.", source=owner_source, execution_adapter=adapter),
            SkillDefinition("quality", SkillOrigin.OWNER_FRIEND, "assurance", "Validate outputs with tests and evidence.", source=owner_source, execution_adapter=adapter),

            SkillDefinition("research-curation", SkillOrigin.LEGACY, "knowledge", "Curate research artifacts with provenance and quality checks.", source=f"{legacy_source}/research_curator", execution_adapter=adapter),
            SkillDefinition("knowledge-graph", SkillOrigin.LEGACY, "knowledge", "Build and inspect linked workspace knowledge relationships.", source=f"{legacy_source}/research_curator", execution_adapter=adapter),
            SkillDefinition("house-command-dispatch", SkillOrigin.LEGACY, "operations", "Dispatch governed house commands through the preserved command boundary.", source=f"{legacy_source}/house_command", execution_adapter=adapter),
            SkillDefinition("github-integration", SkillOrigin.LEGACY, "integration", "Inspect repository and delivery context through governed GitHub integration.", source=f"{legacy_source}/research_os_api", execution_adapter=adapter),
            SkillDefinition("google-workspace-integration", SkillOrigin.LEGACY, "integration", "Work with Google Workspace through owner-authorized integration boundaries.", source=f"{legacy_source}/research_os_api", execution_adapter=adapter),
            SkillDefinition("cloud-conversation-sync", SkillOrigin.LEGACY, "memory", "Synchronize conversation records without replacing local ownership rules.", source=f"{legacy_source}/research_os_api", execution_adapter=adapter),
            SkillDefinition("orchestration-observability", SkillOrigin.LEGACY, "quality", "Inspect orchestration status, evidence, and operational signals.", source=f"{legacy_source}/research_os_api", execution_adapter=adapter),
            SkillDefinition("completion-crew", SkillOrigin.LEGACY, "orchestration", "Coordinate completion checks for bounded delivery work.", source=f"{legacy_source}/research_os_api", execution_adapter=adapter),
            SkillDefinition("quality-gate", SkillOrigin.LEGACY, "quality", "Run release-readiness and contract validation gates.", source=f"{legacy_source}/research_os_api", execution_adapter=adapter),
            SkillDefinition("file-audit-6x6", SkillOrigin.LEGACY, "quality", "Audit candidate repository files using adaptive 6^6 evidence rules.", source=f"{legacy_source}/file_audit_v6x6.py", execution_adapter=adapter),
            SkillDefinition("developer-identity", SkillOrigin.LEGACY, "security", "Verify short-lived trusted developer identity assertions.", source=f"{legacy_source}/research_os_api/developer_identity.py", execution_adapter=adapter),
            SkillDefinition("provider-readiness", SkillOrigin.LEGACY, "providers", "Inspect provider readiness without exposing credentials.", source=f"{legacy_source}/research_os_api/provider_readiness.py", execution_adapter=adapter),
            SkillDefinition("owner-policy", SkillOrigin.LEGACY, "security", "Apply owner-managed permission and approval policy.", source="owner_special/research_os_friend/policy.py", execution_adapter=adapter),
            SkillDefinition("evidence-recording", SkillOrigin.LEGACY, "quality", "Record credential-redacted execution evidence and audit events.", source="owner_special/research_os_friend/evidence.py", execution_adapter=adapter),
            SkillDefinition("v3-bridge", SkillOrigin.LEGACY, "integration", "Bridge preserved Owner/Friend capabilities into V3 contracts without a second master.", source="owner_special/research_os_friend/v3_bridge.py", execution_adapter=adapter),
        )

    def list(self) -> tuple[SkillDefinition, ...]:
        return self._skills

    def get(self, name: str) -> SkillDefinition | None:
        return self._by_name.get(name)

    def by_origin(self, origin: SkillOrigin) -> tuple[SkillDefinition, ...]:
        return tuple(skill for skill in self._skills if skill.origin is origin)

    def by_capability(self, capability: str) -> tuple[SkillDefinition, ...]:
        wanted = capability.strip().lower()
        return tuple(skill for skill in self._skills if skill.capability.lower() == wanted)

    def origins(self) -> tuple[SkillOrigin, ...]:
        return tuple(origin for origin in SkillOrigin if self.by_origin(origin))

    def conversation_context(self) -> str:
        lines = [
            "Unified Research OS skills (V3 is the single execution authority):"
        ]
        for skill in self._skills:
            lines.append(
                f"- {skill.name} [{skill.origin.value}/{skill.capability}; {skill.runtime_mode}; {skill.execution_adapter}]: "
                f"{skill.description}"
            )
        lines.append(
            "A listed native skill is executable through a V3 core path or governed V3 adapter. "
            "Never claim execution unless an explicit V3 runtime/tool/agent result is supplied."
        )
        return "\n".join(lines)
