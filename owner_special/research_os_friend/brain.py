from __future__ import annotations

from .models import FriendRequest, ScaleProfile
from .v3_bridge import V3Bridge


class FriendBrain:
    """Friend request adapter; V3 UnifiedMaster owns scale selection."""

    def __init__(self, bridge: V3Bridge) -> None:
        self.bridge = bridge

    @staticmethod
    def estimated_leaf_tasks(request: FriendRequest) -> int:
        # Complexity is translated into a workload estimate, not a scale.
        # Explicit helper_budget represents a larger requested logical workload.
        complexity_work = max(1, int(request.complexity)) ** 2
        helper_work = max(0, int(request.helper_budget))
        return max(complexity_work, helper_work)

    def select_scale(self, request: FriendRequest) -> ScaleProfile:
        decision = self.bridge.master_decision(
            estimated_leaf_tasks=self.estimated_leaf_tasks(request),
            risk=request.risk,
            parallelism=request.parallelism,
        )

        if not decision.get("available"):
            raise RuntimeError(
                "V3 UnifiedMaster scale authority unavailable: "
                + str(decision.get("reason", "unknown"))
            )

        return ScaleProfile(str(decision["scale"]))

    def capabilities_for(self, request: FriendRequest) -> tuple[str, ...]:
        capabilities = [
            "understand",
            "plan",
            "respond",
            "evidence",
            "v3-unified-master",
        ]

        if request.requested_skills:
            capabilities.append("skills")
        if request.requested_tools:
            capabilities.append("tools")
        if request.complexity >= 4:
            capabilities.append("decompose")
        if request.parallelism >= 3:
            capabilities.append("parallel-route")
        if request.helper_budget >= 1_000_000:
            capabilities.append("large-logical-helper-routing")
        if request.risk >= 4:
            capabilities.append("extra-validation")

        return tuple(capabilities)
