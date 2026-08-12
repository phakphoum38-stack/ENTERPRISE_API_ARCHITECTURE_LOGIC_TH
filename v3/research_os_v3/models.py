from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ScaleTier(str, Enum):
    TIER_3_1 = "3^1"
    TIER_3_3 = "3^3"
    TIER_3_6 = "3^6"
    TIER_6_3 = "6^3"
    TIER_6_6 = "6^6"


@dataclass(frozen=True)
class ScaleProfile:
    tier: ScaleTier
    fanout: int
    depth: int

    @property
    def capacity(self) -> int:
        return self.fanout ** self.depth


# Ordered by capacity. BrainCore always picks the smallest safe profile.
SCALE_PROFILES: tuple[ScaleProfile, ...] = (
    ScaleProfile(ScaleTier.TIER_3_1, fanout=3, depth=1),
    ScaleProfile(ScaleTier.TIER_3_3, fanout=3, depth=3),
    ScaleProfile(ScaleTier.TIER_6_3, fanout=6, depth=3),
    ScaleProfile(ScaleTier.TIER_3_6, fanout=3, depth=6),
    ScaleProfile(ScaleTier.TIER_6_6, fanout=6, depth=6),
)


@dataclass(frozen=True)
class Workload:
    estimated_leaf_tasks: int = 1
    risk: int = 1
    parallelism: int = 1

    def normalized_demand(self) -> int:
        tasks = max(1, self.estimated_leaf_tasks)
        risk_multiplier = 1 if self.risk <= 2 else 2
        parallel_multiplier = 1 if self.parallelism <= 1 else min(self.parallelism, 6)
        return tasks * risk_multiplier * parallel_multiplier


@dataclass(frozen=True)
class OrchestrationDecision:
    profile: ScaleProfile
    provider: str
    demand: int
    reason: str
