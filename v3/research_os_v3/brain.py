from __future__ import annotations

from typing import Iterable

from .models import SCALE_PROFILES, ScaleProfile, Workload
from .research_planner import ResearchPlan, ResearchPlanner


class BrainCore:
    """Research decision boundary plus logical execution-scale selection.

    Brain produces intent and planning data; it never calls providers or
    executes work directly. The orchestrator remains the execution authority.
    """

    def __init__(self, planner: ResearchPlanner | None = None) -> None:
        self._planner = planner or ResearchPlanner()

    def select_profile(self, workload: Workload) -> tuple[ScaleProfile, int, str]:
        demand = workload.normalized_demand()
        for profile in SCALE_PROFILES:
            if demand <= profile.capacity:
                return profile, demand, f"smallest profile satisfying demand={demand}"

        profile = SCALE_PROFILES[-1]
        return profile, demand, (
            f"demand={demand} exceeds logical capacity={profile.capacity}; "
            "use maximum profile with queue/backpressure"
        )

    def create_research_plan(
        self,
        question: str,
        *,
        objective: str | None = None,
        sub_questions: Iterable[str] = (),
        assumptions: Iterable[str] = (),
    ) -> ResearchPlan:
        """Turn a research question into a validated task graph.

        Provider selection and execution are intentionally delegated to the
        Unified Master Orchestrator.
        """
        return self._planner.plan(
            question,
            objective=objective,
            sub_questions=sub_questions,
            assumptions=assumptions,
        )
