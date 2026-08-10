#!/usr/bin/env python3
"""Research OS AI Brain Skill -> Tool execution bridge.

Phase 4 turns a SkillDefinition into a governed execution request. It resolves
skill dependencies, checks skill-level permissions, deterministically matches a
ready tool, delegates the actual call to the hardened ExecutionController and
then verifies declared evidence before the skill is considered complete.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable, Mapping

from v2_brain_core import ResearchOSBrain
from v2_execution_hardening import (
    HardenedExecutionController,
    SecretAwareExecutionRequest,
)
from v2_skill_registry import SkillDefinition, SkillRegistry
from v2_tool_registry import ToolRegistry


SKILL_EXECUTION_CONTRACT = "brain-skill-tool-execution-phase-4"


@dataclass(frozen=True)
class SkillExecutionRequest:
    session_id: str
    skill_id: str
    action: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    granted_permissions: tuple[str, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)
    approved: bool = False
    dry_run: bool = False
    tool_id: str | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None
    secret_values: tuple[str, ...] = ()


@dataclass(frozen=True)
class SkillExecutionResult:
    contract: str
    session_id: str
    skill_id: str
    status: str
    dependency_order: tuple[str, ...]
    selected_tool_id: str | None
    tool_match: Mapping[str, Any]
    execution: Mapping[str, Any] | None
    verification: Mapping[str, Any] | None
    blocked_reasons: tuple[str, ...] = ()


def _collect_evidence(value: Any, target: dict[str, Any]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            name = str(key)
            if name not in target and child not in (None, "", [], {}):
                target[name] = child
            _collect_evidence(child, target)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _collect_evidence(child, target)


class SkillExecutor:
    def __init__(
        self,
        *,
        skills: SkillRegistry,
        tools: ToolRegistry,
        execution: HardenedExecutionController,
        brain: ResearchOSBrain,
    ) -> None:
        self.skills = skills
        self.tools = tools
        self.execution = execution
        self.brain = brain

    @staticmethod
    def _missing_permissions(
        skill: SkillDefinition,
        granted_permissions: Iterable[str],
    ) -> tuple[str, ...]:
        granted = {item.casefold().strip() for item in granted_permissions if item.strip()}
        return tuple(
            permission
            for permission in skill.permissions
            if permission.casefold().strip() not in granted
        )

    def resolve_tool(
        self,
        skill: SkillDefinition,
        *,
        requested_tool_id: str | None = None,
    ) -> dict[str, Any]:
        named = tuple(dict.fromkeys(skill.required_tools))
        capability_match = self.tools.match_capabilities(
            skill.required_tool_capabilities,
            ready_only=True,
        )
        capability_candidates = set(capability_match["candidates"])

        if len(named) > 1:
            return {
                "matched": False,
                "selected_tool_id": None,
                "named_tools": named,
                "capability_match": capability_match,
                "blocked_reasons": (
                    "multi-tool skill requires orchestration; Phase 4 executes one tool step at a time",
                ),
            }

        if named:
            try:
                named_item = self.tools.describe(named[0])
            except ValueError:
                named_item = None
            named_candidates = {named[0]} if named_item and named_item["ready"] else set()
        else:
            named_candidates = set()

        if named and skill.required_tool_capabilities:
            candidates = sorted(named_candidates & capability_candidates)
        elif named:
            candidates = sorted(named_candidates)
        elif skill.required_tool_capabilities:
            candidates = sorted(capability_candidates)
        elif requested_tool_id:
            try:
                item = self.tools.describe(requested_tool_id)
            except ValueError:
                item = None
            candidates = [requested_tool_id] if item and item["ready"] else []
        else:
            candidates = []

        if requested_tool_id:
            candidates = [item for item in candidates if item == requested_tool_id]

        blocked: list[str] = []
        if named and not named_candidates:
            blocked.append(f"required tool unavailable: {named[0]}")
        for capability in capability_match["missing_capabilities"]:
            blocked.append(f"required tool capability unavailable: {capability}")
        if requested_tool_id and not candidates:
            blocked.append(f"requested tool does not satisfy skill requirements: {requested_tool_id}")
        if not named and not skill.required_tool_capabilities and not requested_tool_id:
            blocked.append("skill has no executable tool requirement")
        if not candidates and not blocked:
            blocked.append("no ready tool satisfies the skill contract")

        return {
            "matched": bool(candidates),
            "selected_tool_id": candidates[0] if candidates else None,
            "candidates": candidates,
            "named_tools": named,
            "required_tool_capabilities": skill.required_tool_capabilities,
            "capability_match": capability_match,
            "blocked_reasons": tuple(blocked),
        }

    def execute(self, request: SkillExecutionRequest) -> SkillExecutionResult:
        if not request.session_id.strip():
            raise ValueError("session_id is required")
        if not request.action.strip():
            raise ValueError("skill action is required")

        skill = self.skills.get(request.skill_id)
        dependency_order = self.skills.resolve_dependencies((skill.skill_id,))
        blocked: list[str] = []

        missing_permissions = self._missing_permissions(skill, request.granted_permissions)
        blocked.extend(f"skill permission missing: {item}" for item in missing_permissions)

        tool_match = self.resolve_tool(skill, requested_tool_id=request.tool_id)
        blocked.extend(str(item) for item in tool_match.get("blocked_reasons", ()))
        selected_tool_id = tool_match.get("selected_tool_id")

        if blocked or not selected_tool_id:
            return SkillExecutionResult(
                contract=SKILL_EXECUTION_CONTRACT,
                session_id=request.session_id,
                skill_id=request.skill_id,
                status="blocked",
                dependency_order=dependency_order,
                selected_tool_id=None,
                tool_match=tool_match,
                execution=None,
                verification=None,
                blocked_reasons=tuple(dict.fromkeys(blocked)),
            )

        execution_result = self.execution.execute(
            SecretAwareExecutionRequest(
                session_id=request.session_id,
                tool_id=str(selected_tool_id),
                action=request.action,
                payload=dict(request.payload),
                granted_permissions=request.granted_permissions,
                evidence=dict(request.evidence),
                approved=request.approved,
                dry_run=request.dry_run,
                idempotency_key=request.idempotency_key,
                correlation_id=request.correlation_id,
                secret_values=request.secret_values,
            )
        )
        execution_payload = asdict(execution_result)

        if execution_result.status != "completed":
            return SkillExecutionResult(
                contract=SKILL_EXECUTION_CONTRACT,
                session_id=request.session_id,
                skill_id=request.skill_id,
                status=execution_result.status,
                dependency_order=dependency_order,
                selected_tool_id=str(selected_tool_id),
                tool_match=tool_match,
                execution=execution_payload,
                verification=None,
            )

        evidence: dict[str, Any] = dict(request.evidence)
        evidence.update(
            {
                "skill_id": request.skill_id,
                "tool_id": str(selected_tool_id),
                "execution_status": execution_result.status,
            }
        )
        if execution_result.output is not None:
            _collect_evidence(execution_result.output, evidence)

        verification = self.brain.verify(
            session_id=request.session_id,
            evidence=evidence,
            required_evidence=skill.required_evidence,
        )
        verification_payload = asdict(verification)
        return SkillExecutionResult(
            contract=SKILL_EXECUTION_CONTRACT,
            session_id=request.session_id,
            skill_id=request.skill_id,
            status="verified" if verification.verified else "verification_failed",
            dependency_order=dependency_order,
            selected_tool_id=str(selected_tool_id),
            tool_match=tool_match,
            execution=execution_payload,
            verification=verification_payload,
            blocked_reasons=tuple(
                f"evidence missing: {item}" for item in verification.missing_evidence
            ),
        )

    def dashboard(self) -> dict[str, Any]:
        return {
            "contract": SKILL_EXECUTION_CONTRACT,
            "dependency_resolution": "dependency_first",
            "tool_selection": "deterministic_capability_match",
            "execution_boundary": "hardened_permissioned_controller",
            "post_execution_verification": True,
            "multi_tool_skills": "orchestration_required",
        }
