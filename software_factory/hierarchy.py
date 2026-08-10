from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil
from typing import Iterable


@dataclass(frozen=True)
class PowerProfile:
    """Logical hierarchy profile such as 1^3, 3^3, 6^3, or 6^6.

    The profile defines maximum logical capacity. Runtime nodes are created lazily
    from workload demand instead of materializing the entire tree.
    """

    width: int
    depth: int

    def __post_init__(self) -> None:
        if self.width < 1:
            raise ValueError("width must be >= 1")
        if self.depth < 1:
            raise ValueError("depth must be >= 1")

    @property
    def capacity(self) -> int:
        return self.width ** self.depth

    @property
    def label(self) -> str:
        return f"{self.width}^{self.depth}"


SUPPORTED_PROFILES: tuple[PowerProfile, ...] = (
    PowerProfile(1, 3),
    PowerProfile(3, 3),
    PowerProfile(6, 3),
    PowerProfile(6, 6),
)


@dataclass
class OrchestratorNode:
    node_id: str
    level: int
    children: list["OrchestratorNode"] = field(default_factory=list)
    assigned_versions: list[str] = field(default_factory=list)

    def walk(self) -> Iterable["OrchestratorNode"]:
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass(frozen=True)
class HierarchyPlan:
    profile: PowerProfile
    requested_factories: int
    active_factories: int
    active_orchestrators: int
    root: OrchestratorNode


class AdaptiveHierarchyPlanner:
    """Build only the orchestrator nodes required by the current workload."""

    def __init__(self, profiles: tuple[PowerProfile, ...] = SUPPORTED_PROFILES) -> None:
        if not profiles:
            raise ValueError("at least one power profile is required")
        self.profiles = tuple(sorted(profiles, key=lambda item: item.capacity))

    def choose_profile(self, requested_factories: int) -> PowerProfile:
        if requested_factories < 1:
            raise ValueError("requested_factories must be >= 1")
        for profile in self.profiles:
            if requested_factories <= profile.capacity:
                return profile
        raise ValueError(
            f"workload requires {requested_factories} factories, above maximum "
            f"logical capacity {self.profiles[-1].capacity}"
        )

    def plan(self, versions: Iterable[str]) -> HierarchyPlan:
        normalized = tuple(dict.fromkeys(version.strip() for version in versions if version.strip()))
        if not normalized:
            raise ValueError("at least one version is required")

        profile = self.choose_profile(len(normalized))
        root = OrchestratorNode(node_id="master:l0", level=0)
        leaves = self._grow_lazy_tree(root, profile, len(normalized))

        for version, leaf in zip(normalized, leaves, strict=True):
            leaf.assigned_versions.append(version)

        return HierarchyPlan(
            profile=profile,
            requested_factories=len(normalized),
            active_factories=len(leaves),
            active_orchestrators=sum(1 for node in root.walk()),
            root=root,
        )

    def _grow_lazy_tree(
        self,
        root: OrchestratorNode,
        profile: PowerProfile,
        required_leaves: int,
    ) -> list[OrchestratorNode]:
        current = [root]
        remaining = required_leaves

        for level in range(1, profile.depth + 1):
            capacity_below = profile.width ** (profile.depth - level)
            required_nodes = ceil(remaining / capacity_below)
            next_level: list[OrchestratorNode] = []

            for parent_index, parent in enumerate(current):
                if len(next_level) >= required_nodes:
                    break
                slots_left = required_nodes - len(next_level)
                child_count = min(profile.width, slots_left)
                for child_index in range(child_count):
                    child = OrchestratorNode(
                        node_id=f"{parent.node_id}.{child_index + 1}",
                        level=level,
                    )
                    parent.children.append(child)
                    next_level.append(child)

            current = next_level

        return current[:required_leaves]
