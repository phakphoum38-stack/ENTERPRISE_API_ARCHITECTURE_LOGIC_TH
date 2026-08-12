from __future__ import annotations

from .models import FriendDecision, FriendRequest, ScaleProfile


class DecisionPlanner:
    """Produces reviewable high-level plans without persisting hidden chain-of-thought."""

    def plan(
        self,
        request: FriendRequest,
        *,
        scale: ScaleProfile,
        skills: tuple[str, ...],
        tools: tuple[str, ...],
    ) -> FriendDecision:
        steps = ["understand-owner-request"]
        if skills:
            steps.append("route-skills")
        if tools:
            steps.append("authorize-and-run-tools")
        steps.extend(("produce-answer", "record-evidence"))
        summary = (
            f"Use {scale.value} adaptive capacity; "
            f"skills={len(skills)} tools={len(tools)}; "
            "keep execution owner-scoped and evidence-backed."
        )
        return FriendDecision(
            scale=scale,
            plan=tuple(steps),
            selected_skills=skills,
            selected_tools=tools,
            summary=summary,
        )
