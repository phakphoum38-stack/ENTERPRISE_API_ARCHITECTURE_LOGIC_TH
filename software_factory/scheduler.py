from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ResourceBudget:
    max_active_factories: int = 6
    max_active_agents_per_factory: int = 3

    def __post_init__(self) -> None:
        if self.max_active_factories < 1 or self.max_active_agents_per_factory < 1:
            raise ValueError("resource limits must be positive")


@dataclass
class DynamicResourceScheduler:
    """Admission controller that activates only the work the current budget permits."""

    budget: ResourceBudget = field(default_factory=ResourceBudget)
    _active: set[str] = field(default_factory=set)

    def admit(self, candidates: tuple[str, ...]) -> tuple[str, ...]:
        available = max(0, self.budget.max_active_factories - len(self._active))
        admitted = tuple(version for version in candidates if version not in self._active)[:available]
        self._active.update(admitted)
        return admitted

    def release(self, version: str) -> None:
        self._active.discard(version)

    @property
    def active(self) -> tuple[str, ...]:
        return tuple(sorted(self._active))

    def agent_slots_for(self, version: str, requested: int) -> int:
        if version not in self._active:
            return 0
        return min(max(0, requested), self.budget.max_active_agents_per_factory)
