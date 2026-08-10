from __future__ import annotations

from .models import FriendRequest, ScaleProfile


class FriendBrain:
    """Adaptive logical-capacity selector; workers are activated lazily."""

    def select_scale(self, request: FriendRequest) -> ScaleProfile:
        score = max(1, request.complexity) + max(1, request.risk) + max(1, request.parallelism)
        if score <= 5:
            return ScaleProfile.ONE_CUBED
        if score <= 10:
            return ScaleProfile.THREE_CUBED
        if score <= 18:
            return ScaleProfile.SIX_CUBED
        return ScaleProfile.SIX_TO_SIX

    def capabilities_for(self, request: FriendRequest) -> tuple[str, ...]:
        capabilities = ["understand", "plan", "respond", "evidence"]
        if request.requested_skills:
            capabilities.append("skills")
        if request.requested_tools:
            capabilities.append("tools")
        if request.complexity >= 4:
            capabilities.append("decompose")
        if request.parallelism >= 3:
            capabilities.append("parallel-route")
        if request.risk >= 4:
            capabilities.append("extra-validation")
        return tuple(capabilities)
