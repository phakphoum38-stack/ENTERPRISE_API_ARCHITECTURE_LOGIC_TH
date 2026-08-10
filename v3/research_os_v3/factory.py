from __future__ import annotations

from dataclasses import dataclass

from .models import ScaleProfile


@dataclass(frozen=True)
class FactoryStage:
    name: str
    required: bool = True


@dataclass(frozen=True)
class SoftwareFactoryPlan:
    profile: ScaleProfile
    stages: tuple[FactoryStage, ...]

    @property
    def maximum_leaf_capacity(self) -> int:
        return self.profile.capacity


class SoftwareFactory:
    def plan(self, profile: ScaleProfile) -> SoftwareFactoryPlan:
        return SoftwareFactoryPlan(
            profile=profile,
            stages=(
                FactoryStage("master"),
                FactoryStage("factory"),
                FactoryStage("team"),
                FactoryStage("tests"),
                FactoryStage("release"),
            ),
        )
