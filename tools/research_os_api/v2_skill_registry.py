#!/usr/bin/env python3
"""Research OS AI Brain skill registry.

Skills are executable contracts, not prompt adjectives. This registry owns skill
identity, versioning, capability discovery, dependency ordering, permission
requirements and verification evidence. Execution adapters are intentionally
separate and will attach in a later slice.
"""

from __future__ import annotations

import re
import threading
from dataclasses import asdict, dataclass
from typing import Any, Iterable


_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{2,79}$")
_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][A-Za-z0-9_.-]+)?$")


@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str
    version: str
    name: str
    description: str
    capabilities: tuple[str, ...]
    required_skills: tuple[str, ...] = ()
    required_tools: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    required_evidence: tuple[str, ...] = ()
    owner: str = "Research OS"
    enabled: bool = True


CORE_BRAIN_SKILLS: tuple[SkillDefinition, ...] = (
    SkillDefinition(
        "brain.goal-analysis",
        "1.0.0",
        "Goal Analysis",
        "Extracts explicit goals, constraints, known facts and unknowns before planning.",
        ("goal_analysis", "intent", "known_unknown", "constraints"),
        permissions=("memory.read",),
        required_evidence=("goal", "constraints"),
    ),
    SkillDefinition(
        "brain.risk-assessment",
        "1.0.0",
        "Risk Assessment",
        "Classifies proposed actions by state-change, privilege and operational risk.",
        ("risk_assessment", "approval", "safe_defaults"),
        permissions=("runtime.read",),
        required_evidence=("risk_level", "decision"),
    ),
    SkillDefinition(
        "brain.evidence-verification",
        "1.0.0",
        "Evidence Verification",
        "Checks named evidence before Research OS treats a task as verified.",
        ("verification", "evidence", "definition_of_done", "traceability"),
        permissions=("runtime.read", "memory.read"),
        required_evidence=("verification_result",),
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
            "skill_count": len(skills),
            "ready_count": len(ready),
            "enabled_count": sum(1 for item in skills if item["enabled"]),
            "capabilities": self.capability_catalog(),
            "skills": skills,
            "execution": "contract_only",
        }


SKILLS = SkillRegistry()
