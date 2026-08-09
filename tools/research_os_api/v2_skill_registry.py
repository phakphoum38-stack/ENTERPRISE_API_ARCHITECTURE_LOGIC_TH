#!/usr/bin/env python3
"""Research OS AI Brain skill registry.

Skills are executable operational contracts, not prompt adjectives. The registry
owns identity, versioning, capability discovery, dependency ordering, declared
procedure/preconditions/postconditions/recovery, permissions, tool requirements
and verification evidence. Execution remains a separate governed boundary.
"""

from __future__ import annotations

import re
import threading
from dataclasses import asdict, dataclass
from typing import Any, Iterable


_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{2,79}$")
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?$")
SKILL_REGISTRY_CONTRACT = "brain-skills-phase-10"


@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str
    version: str
    name: str
    description: str
    capabilities: tuple[str, ...]
    required_skills: tuple[str, ...] = ()
    required_tools: tuple[str, ...] = ()
    required_tool_capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    procedure: tuple[str, ...] = ()
    preconditions: tuple[str, ...] = ()
    postconditions: tuple[str, ...] = ()
    recovery: tuple[str, ...] = ()
    owner: str = "Research OS"
    enabled: bool = True


CORE_BRAIN_SKILLS: tuple[SkillDefinition, ...] = (
    SkillDefinition(
        "brain.goal-analysis",
        "1.0.0",
        "Goal Analysis",
        "Extracts explicit goals, constraints, known facts and unknowns before planning.",
        ("goal_analysis", "intent", "known_unknown", "constraints"),
        required_tool_capabilities=("context_engine",),
        permissions=("memory.read", "runtime.read"),
        required_evidence=("objective",),
        procedure=(
            "read the bounded current objective and context",
            "separate explicit goal, constraints, known facts and unknowns",
            "preserve unresolved unknowns instead of guessing",
            "emit only structured goal-analysis evidence",
        ),
        preconditions=("objective is present",),
        postconditions=("goal and unknowns are explicit",),
        recovery=("request or retrieve missing context when an unknown blocks planning",),
    ),
    SkillDefinition(
        "brain.risk-assessment",
        "1.0.0",
        "Risk Assessment",
        "Classifies proposed actions by state-change, privilege and operational risk.",
        ("risk_assessment", "approval", "safe_defaults"),
        permissions=("runtime.read",),
        required_evidence=("risk_level", "decision"),
        procedure=(
            "classify state change, privilege, network, secret, release and production impact",
            "identify required permissions and approval boundary",
            "choose the least-privilege safe action or block",
            "record concise risk evidence without hidden reasoning",
        ),
        preconditions=("proposed action is explicit",),
        postconditions=("risk and approval requirement are explicit",),
        recovery=("fail closed when action impact or authority is unknown",),
    ),
    SkillDefinition(
        "brain.evidence-verification",
        "1.0.0",
        "Evidence Verification",
        "Checks named evidence before Research OS treats a task as verified.",
        ("verification", "evidence", "definition_of_done", "traceability"),
        required_tool_capabilities=("session_inspection",),
        permissions=("runtime.read", "memory.read"),
        required_evidence=("session_id",),
        procedure=(
            "enumerate required evidence from the task/skill contract",
            "compare supplied evidence with each named requirement",
            "mark missing or contradictory evidence explicitly",
            "return verified only when required evidence is sufficient",
        ),
        preconditions=("verification contract is known",),
        postconditions=("verified, failed, or unknown result has evidence gaps listed",),
        recovery=("return unknown rather than pass when evidence is insufficient",),
    ),
)


class SkillRegistry:
    def __init__(self, skills: Iterable[SkillDefinition] = CORE_BRAIN_SKILLS) -> None:
        self._lock = threading.RLock()
        self._skills: dict[str, SkillDefinition] = {}
        for skill in skills:
            self.register(skill)

    @staticmethod
    def _validate(skill: SkillDefinition) -> None:
        if not _ID_RE.fullmatch(skill.skill_id):
            raise ValueError(f"invalid skill_id: {skill.skill_id}")
        if not _VERSION_RE.fullmatch(skill.version):
            raise ValueError(f"invalid skill version: {skill.version}")
        if not skill.name.strip() or not skill.description.strip():
            raise ValueError(f"skill name/description required: {skill.skill_id}")
        if not skill.capabilities:
            raise ValueError(f"skill capabilities required: {skill.skill_id}")
        if skill.skill_id in skill.required_skills:
            raise ValueError(f"skill cannot depend on itself: {skill.skill_id}")
        if len(set(skill.required_tools)) != len(skill.required_tools):
            raise ValueError(f"duplicate required tool: {skill.skill_id}")
        if len(set(skill.required_tool_capabilities)) != len(skill.required_tool_capabilities):
            raise ValueError(f"duplicate required tool capability: {skill.skill_id}")
        for field_name, values in (
            ("capabilities", skill.capabilities),
            ("permissions", skill.permissions),
            ("required_evidence", skill.required_evidence),
            ("procedure", skill.procedure),
            ("preconditions", skill.preconditions),
            ("postconditions", skill.postconditions),
            ("recovery", skill.recovery),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"duplicate {field_name} item: {skill.skill_id}")
            if any(not str(item).strip() for item in values):
                raise ValueError(f"empty {field_name} item: {skill.skill_id}")
        if len(skill.procedure) > 32:
            raise ValueError(f"skill procedure exceeds 32 steps: {skill.skill_id}")

    def register(self, skill: SkillDefinition, *, replace: bool = False) -> dict[str, Any]:
        self._validate(skill)
        with self._lock:
            if skill.skill_id in self._skills and not replace:
                raise ValueError(f"skill already registered: {skill.skill_id}")
            self._skills[skill.skill_id] = skill
            return self.describe(skill.skill_id)

    def unregister(self, skill_id: str) -> dict[str, Any]:
        with self._lock:
            skill = self.get(skill_id)
            self._skills.pop(skill_id, None)
            return asdict(skill)

    def get(self, skill_id: str) -> SkillDefinition:
        with self._lock:
            try:
                return self._skills[skill_id]
            except KeyError as exc:
                raise ValueError(f"unknown skill: {skill_id}") from exc

    def list(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self.describe(skill_id) for skill_id in sorted(self._skills)]

    def discover(
        self,
        *,
        capability: str | None = None,
        permission: str | None = None,
        enabled_only: bool = True,
    ) -> list[dict[str, Any]]:
        cap = capability.casefold().strip() if capability else None
        perm = permission.casefold().strip() if permission else None
        with self._lock:
            matches: list[dict[str, Any]] = []
            for skill in self._skills.values():
                if enabled_only and not skill.enabled:
                    continue
                if cap and cap not in {item.casefold() for item in skill.capabilities}:
                    continue
                if perm and perm not in {item.casefold() for item in skill.permissions}:
                    continue
                matches.append(self.describe(skill.skill_id))
            return sorted(matches, key=lambda item: item["skill_id"])

    def describe(self, skill_id: str) -> dict[str, Any]:
        with self._lock:
            skill = self.get(skill_id)
            missing = [dep for dep in skill.required_skills if dep not in self._skills]
            disabled = [
                dep for dep in skill.required_skills
                if dep in self._skills and not self._skills[dep].enabled
            ]
            return {
                **asdict(skill),
                "ready": bool(skill.enabled and not missing and not disabled),
                "missing_dependencies": missing,
                "disabled_dependencies": disabled,
                "operational_contract": bool(
                    skill.procedure
                    or skill.required_tools
                    or skill.required_tool_capabilities
                    or skill.required_evidence
                ),
            }

    def resolve_dependencies(self, skill_ids: Iterable[str]) -> tuple[str, ...]:
        """Return dependency-first order or fail on missing/cyclic dependencies."""
        requested = tuple(dict.fromkeys(item.strip() for item in skill_ids if item.strip()))
        visiting: set[str] = set()
        visited: set[str] = set()
        ordered: list[str] = []

        def visit(skill_id: str) -> None:
            if skill_id in visited:
                return
            if skill_id in visiting:
                raise ValueError(f"skill dependency cycle detected: {skill_id}")
            skill = self.get(skill_id)
            if not skill.enabled:
                raise ValueError(f"skill disabled: {skill_id}")
            visiting.add(skill_id)
            for dependency in skill.required_skills:
                visit(dependency)
            visiting.remove(skill_id)
            visited.add(skill_id)
            ordered.append(skill_id)

        for skill_id in requested:
            visit(skill_id)
        return tuple(ordered)

    def capability_catalog(self) -> dict[str, list[str]]:
        catalog: dict[str, list[str]] = {}
        for item in self.list():
            if not item["ready"]:
                continue
            for capability in item["capabilities"]:
                catalog.setdefault(capability, []).append(item["skill_id"])
        return {key: sorted(value) for key, value in sorted(catalog.items())}

    def dashboard(self) -> dict[str, Any]:
        skills = self.list()
        ready = [item for item in skills if item["ready"]]
        return {
            "registry": "research_os_skills",
            "contract": SKILL_REGISTRY_CONTRACT,
            "skill_count": len(skills),
            "ready_count": len(ready),
            "enabled_count": sum(1 for item in skills if item["enabled"]),
            "operational_contract_count": sum(1 for item in skills if item["operational_contract"]),
            "capabilities": self.capability_catalog(),
            "skills": skills,
            "execution": "skill_to_tool_executor",
            "hidden_reasoning_in_skill_contract": False,
        }


SKILLS = SkillRegistry()
