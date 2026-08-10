from __future__ import annotations

import math
import os
import uuid
from dataclasses import asdict, dataclass
from typing import Any, Iterable


BRANCH_FACTOR = 6
ELASTIC_TIERS = 6
MAX_LEAF_CAPACITY = BRANCH_FACTOR**ELASTIC_TIERS
DEFAULT_ACTIVE_WORKER_LIMIT = 36
HARD_ACTIVE_WORKER_LIMIT = 1296
MAX_HYPOTHESIS_BRANCHES = 36
COGNITIVE_STAGES = (
    "decompose",
    "retrieve_evidence",
    "branch_hypotheses",
    "cross_critique",
    "safety_verify",
    "synthesize",
)


@dataclass(frozen=True)
class BrainSkill:
    skill_id: str
    name: str
    description: str
    capabilities: tuple[str, ...]
    risk_level: str = "low"
    requires_approval_for_writes: bool = False
    provider_mode: str = "provider_neutral"


class BrainSkillRegistry:
    """Provider-neutral catalog and deterministic skill router."""

    def __init__(self, skills: Iterable[BrainSkill] = ()) -> None:
        self._skills: dict[str, BrainSkill] = {}
        for skill in skills:
            self.register(skill)

    def register(self, skill: BrainSkill) -> None:
        skill_id = skill.skill_id.strip().lower()
        if not skill_id:
            raise ValueError("skill_id is required")
        if skill_id in self._skills:
            raise ValueError(f"duplicate brain skill: {skill_id}")
        self._skills[skill_id] = skill

    def get(self, skill_id: str) -> BrainSkill:
        try:
            return self._skills[skill_id.strip().lower()]
        except KeyError as exc:
            raise ValueError(f"unknown brain skill: {skill_id}") from exc

    def catalog(self) -> list[dict[str, Any]]:
        return [asdict(self._skills[key]) for key in sorted(self._skills)]

    def route(self, objective: str) -> list[str]:
        text = objective.strip().casefold()
        if not text:
            raise ValueError("objective is required")

        selected = {"planning", "reasoning", "critic", "safety"}
        keyword_routes = {
            "memory": ("memory", "remember", "preference", "context", "ความจำ"),
            "knowledge": ("knowledge", "research", "evidence", "citation", "ค้น", "วิจัย"),
            "tool_selection": ("tool", "plugin", "connector", "mcp", "เครื่องมือ"),
            "coordination": ("agent", "orchestrate", "delegate", "team", "ผู้ช่วย"),
            "learning": ("learn", "lesson", "improve", "เรียนรู้", "บทเรียน"),
            "provider_routing": ("provider", "model", "local model", "โมเดล"),
        }
        for skill_id, keywords in keyword_routes.items():
            if any(keyword in text for keyword in keywords):
                selected.add(skill_id)
        return [skill_id for skill_id in self._skills if skill_id in selected]


class AdaptiveHierarchyPolicy:
    """Plan elastic 6^6 capacity without starting every worker."""

    def __init__(self, max_active_workers: int | None = None) -> None:
        configured = max_active_workers
        if configured is None:
            configured = int(
                os.environ.get(
                    "RESEARCH_OS_MAX_ACTIVE_BRAIN_WORKERS",
                    str(DEFAULT_ACTIVE_WORKER_LIMIT),
                )
            )
        if configured < 1 or configured > HARD_ACTIVE_WORKER_LIMIT:
            raise ValueError(
                "max_active_workers must be between 1 "
                f"and {HARD_ACTIVE_WORKER_LIMIT}"
            )
        self.max_active_workers = configured

    def capacity_snapshot(self) -> dict[str, Any]:
        tier_capacity = [BRANCH_FACTOR**tier for tier in range(1, ELASTIC_TIERS + 1)]
        return {
            "architecture": "adaptive_hierarchical_6x6",
            "control_plane_orchestrators": 1,
            "branch_factor": BRANCH_FACTOR,
            "elastic_tiers": ELASTIC_TIERS,
            "tier_leaf_capacity": tier_capacity,
            "max_leaf_capacity": MAX_LEAF_CAPACITY,
            "max_active_workers": self.max_active_workers,
            "hard_active_worker_limit": HARD_ACTIVE_WORKER_LIMIT,
            "activation_mode": "demand_budget_readiness",
            "all_workers_started_by_default": False,
            "intelligence_mode": "compound_branch_critic_synthesis",
            "cognitive_stages": list(COGNITIVE_STAGES),
            "max_hypothesis_branches": MAX_HYPOTHESIS_BRANCHES,
        }

    def plan(
        self,
        *,
        complexity_level: int = 1,
        requested_workers: int | None = None,
        budget_workers: int | None = None,
        ready_workers: int | None = None,
    ) -> dict[str, Any]:
        if complexity_level < 1 or complexity_level > ELASTIC_TIERS:
            raise ValueError(
                f"complexity_level must be between 1 and {ELASTIC_TIERS}"
            )
        desired = BRANCH_FACTOR**complexity_level
        requested = desired if requested_workers is None else int(requested_workers)
        if requested < 1 or requested > MAX_LEAF_CAPACITY:
            raise ValueError(
                f"requested_workers must be between 1 and {MAX_LEAF_CAPACITY}"
            )

        limits = [requested, self.max_active_workers]
        for name, value in (
            ("budget_workers", budget_workers),
            ("ready_workers", ready_workers),
        ):
            if value is None:
                continue
            parsed = int(value)
            if parsed < 1:
                raise ValueError(f"{name} must be at least 1")
            limits.append(parsed)

        active = min(limits)
        active_tiers = 1 if active <= 1 else min(
            ELASTIC_TIERS,
            math.ceil(math.log(active, BRANCH_FACTOR)),
        )
        return {
            "complexity_level": complexity_level,
            "requested_workers": requested,
            "active_workers": active,
            "active_tiers": active_tiers,
            "max_leaf_capacity": MAX_LEAF_CAPACITY,
            "max_active_workers": self.max_active_workers,
            "backpressure_applied": active < requested,
            "activation_mode": "adaptive",
        }


class BrainSkillsEngine:
    """Single owner for skill discovery and adaptive 6^6 planning."""

    def __init__(
        self,
        registry: BrainSkillRegistry | None = None,
        policy: AdaptiveHierarchyPolicy | None = None,
    ) -> None:
        self.registry = registry or default_brain_skill_registry()
        self.policy = policy or AdaptiveHierarchyPolicy()

    def catalog(self) -> dict[str, Any]:
        skills = self.registry.catalog()
        return {
            "provider_mode": "local_or_configured_provider",
            "skill_count": len(skills),
            "skills": skills,
        }

    def capacity_snapshot(self) -> dict[str, Any]:
        return self.policy.capacity_snapshot()

    def plan(
        self,
        objective: str,
        *,
        complexity_level: int = 1,
        requested_workers: int | None = None,
        budget_workers: int | None = None,
        ready_workers: int | None = None,
    ) -> dict[str, Any]:
        objective = objective.strip()
        if not objective:
            raise ValueError("objective is required")
        hierarchy = self.policy.plan(
            complexity_level=complexity_level,
            requested_workers=requested_workers,
            budget_workers=budget_workers,
            ready_workers=ready_workers,
        )
        selected_skills = self.registry.route(objective)
        cognition = self._compound_cognition(
            objective,
            selected_skills=selected_skills,
            hierarchy=hierarchy,
        )
        return {
            "plan_id": str(uuid.uuid4()),
            "objective": objective,
            "selected_skills": selected_skills,
            "hierarchy": hierarchy,
            "cognition": cognition,
            "provider_mode": "local_or_configured_provider",
            "requires_external_api_key": False,
            "provider_execution_requires_credentials": True,
            "writes_require_approval": True,
        }

    def research_instructions(self, plan: dict[str, Any]) -> str:
        """Build bounded quality instructions without exposing hidden reasoning."""
        cognition = plan.get("cognition", {})
        branches = int(cognition.get("hypothesis_branches", 1))
        critic_passes = int(cognition.get("critic_passes", 1))
        return (
            "Use a bounded compound-research process. Decompose the request, gather "
            f"current evidence, compare up to {branches} plausible hypotheses, run "
            f"{critic_passes} critic passes for conflicts and missing evidence, apply "
            "safety checks, then synthesize a concise answer. Cite sources near claims, "
            "separate facts from inference, disclose material uncertainty, and do not "
            "reveal private chain-of-thought."
        )

    @staticmethod
    def _compound_cognition(
        objective: str,
        *,
        selected_skills: list[str],
        hierarchy: dict[str, Any],
    ) -> dict[str, Any]:
        complexity = int(hierarchy["complexity_level"])
        active_workers = int(hierarchy["active_workers"])
        candidate_capacity = BRANCH_FACTOR**complexity
        hypotheses = min(
            MAX_HYPOTHESIS_BRANCHES,
            active_workers,
            candidate_capacity,
        )
        critic_passes = min(BRANCH_FACTOR, max(1, complexity))
        quorum = max(1, math.ceil(hypotheses * 2 / 3))
        text = objective.casefold()
        time_sensitive = any(
            token in text
            for token in (
                "latest",
                "current",
                "today",
                "news",
                "ล่าสุด",
                "ปัจจุบัน",
                "วันนี้",
                "ข่าว",
            )
        )
        evidence_required = "knowledge" in selected_skills or time_sensitive
        return {
            "mode": "compound_6x6",
            "stages": list(COGNITIVE_STAGES),
            "candidate_capacity": candidate_capacity,
            "hypothesis_branches": hypotheses,
            "critic_passes": critic_passes,
            "consensus_quorum": quorum,
            "evidence_required": evidence_required,
            "web_search_recommended": evidence_required or time_sensitive,
            "confidence_threshold": 0.75,
            "bounded": True,
            "hidden_reasoning_exposed": False,
        }


def default_brain_skill_registry() -> BrainSkillRegistry:
    definitions = (
        BrainSkill("planning", "Planning Brain", "Break goals into bounded steps.", ("plan", "dependencies", "priorities")),
        BrainSkill("reasoning", "Reasoning Brain", "Separate facts, assumptions and inferences.", ("analyze", "compare", "infer")),
        BrainSkill("memory", "Memory Brain", "Select relevant short and long-term context.", ("recall", "summarize", "forget")),
        BrainSkill("knowledge", "Knowledge Brain", "Retrieve evidence with provenance.", ("search", "retrieve", "cite")),
        BrainSkill("tool_selection", "Tool Brain", "Choose tools by capability, health and permission.", ("discover", "select", "fallback")),
        BrainSkill("coordination", "Agent Brain", "Coordinate agents and handoffs.", ("delegate", "handoff", "orchestrate")),
        BrainSkill("critic", "Critic Brain", "Check completeness, conflicts and evidence.", ("review", "validate", "score")),
        BrainSkill("safety", "Safety Brain", "Apply permission and approval boundaries.", ("authorize", "classify_risk", "require_approval"), "high", True),
        BrainSkill("learning", "Learning Brain", "Create reviewable lesson candidates without self-modifying code.", ("extract_lesson", "propose", "audit"), "medium", True),
        BrainSkill("provider_routing", "Provider Brain", "Route to local or configured compatible providers.", ("route_provider", "health", "budget")),
    )
    return BrainSkillRegistry(definitions)


BRAIN = BrainSkillsEngine()

