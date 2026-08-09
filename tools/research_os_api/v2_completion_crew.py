from __future__ import annotations

from agent_platform import AgentDefinition, AgentRegistry


COMPLETION_CREW: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        "v2_workspace_engineer",
        "V2 Workspace Engineer",
        "Temporary V2 completion agent for workspace boundaries, knowledge indexing, provenance, conflict detection and import/export.",
        (
            "workspace_engine",
            "knowledge_index",
            "unified_search",
            "provenance",
            "deduplicate",
            "conflict_detection",
            "workspace_export",
            "workspace_import",
        ),
        (
            "source.read",
            "source.write.with_confirmation",
            "knowledge.read",
            "knowledge.write.with_confirmation",
            "documents.read",
        ),
        "shared:v2-workspace-engineer",
        provider_preferences=("openai-compatible", "local", "gemini", "anthropic"),
        model_preferences=("coding", "reasoning"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_agent_center_engineer",
        "V2 Agent Center Engineer",
        "Temporary V2 completion agent for Flutter Agent Center V2, orchestration graph, approval inbox and integration tests.",
        (
            "agent_center_v2",
            "flutter_ui",
            "orchestration_graph",
            "approval_inbox",
            "live_timeline",
            "ui_integration_test",
            "accessibility",
        ),
        (
            "source.read",
            "source.write.with_confirmation",
            "runtime.read",
        ),
        "shared:v2-agent-center-engineer",
        provider_preferences=("openai-compatible", "local", "gemini"),
        model_preferences=("coding", "ui"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_api_compat_engineer",
        "V2 API Compatibility Engineer",
        "Temporary V2 completion agent for API V2 namespace, versioned schemas, compatibility, pagination and OpenAPI tests.",
        (
            "api_v2",
            "compatibility",
            "openapi",
            "schema_versioning",
            "pagination",
            "error_contract",
            "migration_test",
        ),
        (
            "source.read",
            "source.write.with_confirmation",
            "runtime.read",
        ),
        "shared:v2-api-compat-engineer",
        provider_preferences=("openai-compatible", "local", "gemini"),
        model_preferences=("coding", "reasoning"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_reliability_release_engineer",
        "V2 Reliability & Release Engineer",
        "Temporary V2 completion agent for observability, diagnostics, failure injection, installer upgrade/rollback and release evidence.",
        (
            "observability",
            "structured_logs",
            "diagnostics",
            "failure_injection",
            "performance_baseline",
            "installer_upgrade",
            "rollback",
            "release_manifest",
            "production_health",
        ),
        (
            "source.read",
            "source.write.with_confirmation",
            "runtime.read",
            "release.read",
            "release.write.with_confirmation",
        ),
        "shared:v2-reliability-release-engineer",
        provider_preferences=("openai-compatible", "local", "gemini", "anthropic"),
        model_preferences=("coding", "reasoning"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
)


def register_completion_crew(registry: AgentRegistry) -> list[dict[str, object]]:
    """Register fresh V2-only helpers without reusing or replacing active agents."""
    registered: list[dict[str, object]] = []
    for agent in COMPLETION_CREW:
        try:
            registry.get(agent.agent_id)
        except ValueError:
            registered.append(registry.register(agent))
        else:
            registered.append(registry.describe(agent.agent_id))
    return registered
