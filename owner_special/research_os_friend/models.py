from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ScaleProfile(str, Enum):
    ONE_CUBED = "1^3"
    THREE_CUBED = "3^3"
    SIX_CUBED = "6^3"
    SIX_TO_SIX = "6^6"
    FAST_MILLION = "fast-1m"

    @property
    def logical_capacity(self) -> int:
        return {
            ScaleProfile.ONE_CUBED: 1,
            ScaleProfile.THREE_CUBED: 27,
            ScaleProfile.SIX_CUBED: 216,
            ScaleProfile.SIX_TO_SIX: 46656,
            ScaleProfile.FAST_MILLION: 1_000_000,
        }[self]


@dataclass(frozen=True)
class FriendRequest:
    owner_id: str
    text: str
    profile_id: str = "default"
    session_id: str = "default"
    complexity: int = 1
    risk: int = 1
    parallelism: int = 1
    helper_budget: int = 0
    requested_skills: tuple[str, ...] = ()
    requested_tools: tuple[str, ...] = ()


@dataclass(frozen=True)
class FriendDecision:
    scale: ScaleProfile
    plan: tuple[str, ...]
    selected_skills: tuple[str, ...]
    selected_tools: tuple[str, ...]
    summary: str

    @property
    def maximum_leaf_capacity(self) -> int:
        return self.scale.logical_capacity


@dataclass(frozen=True)
class FriendResponse:
    text: str
    decision: FriendDecision
    provider: str
    memory_items: int
    evidence_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
