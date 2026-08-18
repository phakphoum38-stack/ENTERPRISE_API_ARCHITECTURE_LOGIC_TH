from __future__ import annotations

from types import MappingProxyType

_DOMAINS = (
    "architecture",
    "research_core",
    "tools_evidence",
    "runtime",
    "api_security",
    "quality_ci",
)

AGENT_MATRIX = MappingProxyType({
    domain: tuple(f"{domain}.agent_{i}" for i in range(1, 7))
    for domain in _DOMAINS
})

GUARDIANS = (
    "e2e_guardian",
    "production_guardian",
    "quality_guardian",
)


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
