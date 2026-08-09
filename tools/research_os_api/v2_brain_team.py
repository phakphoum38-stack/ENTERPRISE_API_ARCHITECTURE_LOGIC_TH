#!/usr/bin/env python3
"""Research OS AI Brain engineering team.

These are runtime agent contracts used to divide Brain Core engineering work into
independent responsibilities. They do not pretend to be external autonomous
workers; Research OS can route/plumb model sessions to these roles through the
existing AgentRegistry and permission model.
"""

from __future__ import annotations

from agent_platform import AgentDefinition, AgentRegistry


BRAIN_TEAM: tuple[AgentDefinition, ...] = (
    AgentDefinition(
        "v2_brain_coordinator",
        "AI Brain Coordinator",
        "Coordinates Brain Core architecture, task decomposition, dependency order and handoffs across the brain engineering team.",
        ("brain_coordination", "task_decomposition", "dependency_planning", "handoff", "architecture"),
        ("source.read", "memory.read"),
        "shared:v2-brain-coordinator",
        provider_preferences=("openai-compatible", "local", "gemini", "anthropic"),
        model_preferences=("reasoning", "coding"),
        fallback_agents=(),
        permission_profile="standard",
    ),
    AgentDefinition(
        "v2_brain_architect",
        "AI Brain Architect",
        "Owns Brain Core boundaries, state-machine contracts, One Truth integration and model-independent architecture.",
        ("brain_architecture", "architecture", "state_machine", "one_truth", "interface_design"),
        ("source.read", "source.write.with_confirmation", "memory.read"),
        "shared:v2-brain-architect",
        provider_preferences=("openai-compatible", "local", "anthropic", "gemini"),
        model_preferences=("reasoning", "coding"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_context_engineer",
        "Context & Perception Engineer",
        "Owns context assembly, intent extraction, known/unknown tracking, constraints and context-budget boundaries.",
        ("context_engine", "intent", "known_unknown", "constraints", "context_budget", "perception"),
        ("source.read", "source.write.with_confirmation", "memory.read", "knowledge.read"),
        "shared:v2-context-engineer",
        provider_preferences=("openai-compatible", "local", "gemini", "anthropic"),
        model_preferences=("reasoning", "general"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_reasoning_planner",
        "Reasoning & Planning Engineer",
        "Owns explicit plan contracts, goal decomposition, dependency reasoning, uncertainty and auditable decision summaries without exposing hidden chain-of-thought.",
        ("planning", "goal_decomposition", "dependency_reasoning", "uncertainty", "decision_summary", "strategy"),
        ("source.read", "source.write.with_confirmation", "memory.read"),
        "shared:v2-reasoning-planner",
        provider_preferences=("openai-compatible", "anthropic", "local", "gemini"),
        model_preferences=("reasoning",),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_capability_skill_engineer",
        "Capability & Skill Engineer",
        "Owns capability graph, skill contracts, skill discovery, dependency/version rules and future skill composition.",
        ("capability_graph", "skill_registry", "skill_contract", "skill_discovery", "skill_versioning", "skill_composition"),
        ("source.read", "source.write.with_confirmation", "memory.read"),
        "shared:v2-capability-skill-engineer",
        provider_preferences=("openai-compatible", "local", "gemini", "anthropic"),
        model_preferences=("coding", "reasoning"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_memory_knowledge_engineer",
        "Memory & Knowledge Engineer",
        "Owns working memory, project memory adapters, knowledge retrieval, provenance, freshness and conflict-aware recall.",
        ("working_memory", "project_memory", "knowledge", "retrieval", "provenance", "freshness", "conflict_resolution"),
        ("source.read", "source.write.with_confirmation", "memory.read", "knowledge.read", "knowledge.write.with_confirmation"),
        "shared:v2-memory-knowledge-engineer",
        provider_preferences=("local", "openai-compatible", "gemini", "anthropic"),
        model_preferences=("reasoning", "general"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_tool_execution_engineer",
        "Tool & Execution Engineer",
        "Owns tool registry interfaces, execution state, observation loops, dry-run boundaries, idempotency and adapter contracts.",
        ("tool_registry", "execution_controller", "observation_loop", "dry_run", "idempotency", "adapter_contract"),
        ("source.read", "source.write.with_confirmation", "runtime.read", "memory.read"),
        "shared:v2-tool-execution-engineer",
        provider_preferences=("openai-compatible", "local", "gemini"),
        model_preferences=("coding", "reasoning"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_security_policy_engineer",
        "Security & Policy Engineer",
        "Owns permission evaluation, trust boundaries, secret redaction, safe defaults and approval-policy integration.",
        ("permission_engine", "policy", "security", "trust_boundary", "secret_redaction", "approval", "safe_defaults"),
        ("source.read", "source.write.with_confirmation", "runtime.read", "memory.read"),
        "shared:v2-security-policy-engineer",
        provider_preferences=("openai-compatible", "local", "anthropic", "gemini"),
        model_preferences=("reasoning", "coding"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_verification_evidence_engineer",
        "Verification & Evidence Engineer",
        "Owns evidence requirements, verification gates, exact-state checks, completion criteria and claim-to-evidence traceability.",
        ("verification", "evidence", "definition_of_done", "traceability", "exact_state", "quality_gate"),
        ("source.read", "source.write.with_confirmation", "runtime.read", "memory.read"),
        "shared:v2-verification-evidence-engineer",
        provider_preferences=("openai-compatible", "local", "gemini", "anthropic"),
        model_preferences=("reasoning", "coding"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_reliability_recovery_engineer",
        "Reliability & Recovery Engineer",
        "Owns retry policy, interruption recovery, checkpoints, rollback contracts, resilience tests and degraded-mode behavior.",
        ("reliability", "recovery", "retry_policy", "checkpoint", "resume", "rollback", "graceful_degradation"),
        ("source.read", "source.write.with_confirmation", "runtime.read", "memory.read"),
        "shared:v2-reliability-recovery-engineer",
        provider_preferences=("openai-compatible", "local", "gemini", "anthropic"),
        model_preferences=("coding", "reasoning"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_developer_intelligence_engineer",
        "Universal Developer Intelligence Engineer",
        "Owns developer capability taxonomy, language/framework discovery, repository intelligence and extensible engineering knowledge interfaces.",
        ("developer_intelligence", "language_registry", "framework_registry", "repository_intelligence", "code", "debug", "build", "test"),
        ("source.read", "source.write.with_confirmation", "runtime.read", "memory.read", "knowledge.read"),
        "shared:v2-developer-intelligence-engineer",
        provider_preferences=("openai-compatible", "local", "gemini", "anthropic"),
        model_preferences=("coding", "reasoning"),
        fallback_agents=(),
        permission_profile="write_confirmed",
    ),
    AgentDefinition(
        "v2_brain_reviewer",
        "Independent AI Brain Reviewer",
        "Independent read-only reviewer for architecture drift, unsafe assumptions, missing tests, unsupported claims and cross-module consistency.",
        ("independent_review", "architecture_review", "test_review", "security_review", "consistency", "unsupported_claim_detection"),
        ("source.read", "runtime.read", "memory.read", "knowledge.read"),
        "shared:v2-brain-reviewer",
        provider_preferences=("anthropic", "openai-compatible", "local", "gemini"),
        model_preferences=("reasoning",),
        fallback_agents=(),
        permission_profile="read_only",
    ),
)


BRAIN_TEAM_IDS = tuple(agent.agent_id for agent in BRAIN_TEAM)


def register_brain_team(registry: AgentRegistry) -> list[dict[str, object]]:
    """Idempotently register the 12 isolated Brain engineering roles."""
    registered: list[dict[str, object]] = []
    for agent in BRAIN_TEAM:
        try:
            registry.get(agent.agent_id)
        except ValueError:
            registered.append(registry.register(agent))
        else:
            registered.append(registry.describe(agent.agent_id))
    return registered


def brain_team_dashboard(registry: AgentRegistry) -> dict[str, object]:
    """Return readiness/capability summary for only the Brain team."""
    members = [registry.describe(agent_id) for agent_id in BRAIN_TEAM_IDS]
    ready = [member for member in members if member["health"]["ready"]]
    return {
        "team": "research_os_ai_brain_engineering",
        "member_count": len(members),
        "ready_count": len(ready),
        "minimum_required": 10,
        "minimum_satisfied": len(ready) >= 10,
        "members": members,
    }
