from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable

_DOMAINS = (
    "architecture",
    "research_core",
    "tools_evidence",
    "runtime",
    "api_security",
    "quality_ci",
)

# Legacy 6x6 logical matrix retained for compatibility with existing governance checks.
AGENT_MATRIX = MappingProxyType({
    domain: tuple(f"{domain}.agent_{i}" for i in range(1, 7))
    for domain in _DOMAINS
})

GUARDIANS = (
    "e2e_guardian",
    "production_guardian",
    "quality_guardian",
)


@dataclass(frozen=True)
class LogicalAgent:
    agent_id: str
    agent_set: str
    role: str


LOGICAL_AGENT_MATRIX: tuple[LogicalAgent, ...] = (
    LogicalAgent("A1", "orchestrator", "orchestrator"),
    LogicalAgent("A2", "research", "research_discovery"),
    LogicalAgent("A3", "research", "research_synthesis"),
    LogicalAgent("A4", "engineering", "implementation"),
    LogicalAgent("A5", "engineering", "ci_test_debug"),
    LogicalAgent("A6", "workspace", "browser"),
    LogicalAgent("A7", "workspace", "files_workspace"),
    LogicalAgent("A8", "evidence_qa", "evidence_validation"),
    LogicalAgent("A9", "evidence_qa", "regression_release_qa"),
    LogicalAgent("A10", "owner_governance", "owner_governance"),
    LogicalAgent("A11", "owner_governance", "recovery_control"),
)

NORMAL_CONCURRENCY = 4
PARALLEL_CONCURRENCY = 6
MAX_CONCURRENCY = 11


def validate_agent_matrix(matrix=AGENT_MATRIX) -> list[str]:
    errors: list[str] = []
    if len(matrix) != 6:
        errors.append("expected six domains")
    names: list[str] = []
    for domain, agents in matrix.items():
        if not domain:
            errors.append("empty domain")
        if len(agents) != 6:
            errors.append(f"{domain}: expected six agents")
        names.extend(agents)
    if len(names) != len(set(names)):
        errors.append("duplicate agent identifier")
    if len(GUARDIANS) != 3:
        errors.append("expected three guardians")
    return errors


def logical_agent_sets() -> tuple[str, ...]:
    return tuple(dict.fromkeys(agent.agent_set for agent in LOGICAL_AGENT_MATRIX))


def select_logical_agents(required_sets: Iterable[str], concurrency: int = NORMAL_CONCURRENCY) -> tuple[LogicalAgent, ...]:
    """Select the smallest deterministic logical-agent slice for a workload."""
    requested = tuple(dict.fromkeys(required_sets))
    if not requested:
        return (LOGICAL_AGENT_MATRIX[0],)
    limit = max(1, min(concurrency, MAX_CONCURRENCY))
    return tuple(agent for agent in LOGICAL_AGENT_MATRIX if agent.agent_set in requested)[:limit]


def validate_logical_agent_matrix() -> list[str]:
    errors: list[str] = []
    if len(LOGICAL_AGENT_MATRIX) != 11:
        errors.append("expected eleven logical agents")
    if len(logical_agent_sets()) != 6:
        errors.append("expected six logical agent sets")
    ids = [agent.agent_id for agent in LOGICAL_AGENT_MATRIX]
    if len(ids) != len(set(ids)):
        errors.append("duplicate logical agent id")
    if not 1 <= NORMAL_CONCURRENCY <= PARALLEL_CONCURRENCY <= MAX_CONCURRENCY:
        errors.append("invalid concurrency policy")
    return errors


# Fail closed at import time if the governance profile itself is malformed.
if errors := validate_agent_matrix() + validate_logical_agent_matrix():
    raise ValueError("; ".join(errors))
