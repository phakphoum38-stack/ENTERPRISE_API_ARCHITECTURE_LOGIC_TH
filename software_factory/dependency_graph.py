from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class DependencyGraph:
    """Directed dependency graph used to order version/factory work safely."""

    _requires: dict[str, set[str]] = field(default_factory=lambda: defaultdict(set))

    def add_node(self, node: str) -> None:
        self._requires.setdefault(node, set())

    def add_dependency(self, node: str, requires: str) -> None:
        if node == requires:
            raise ValueError("a node cannot depend on itself")
        self.add_node(node)
        self.add_node(requires)
        self._requires[node].add(requires)
        self.topological_order()  # fail immediately on cycles

    def dependencies_of(self, node: str) -> frozenset[str]:
        return frozenset(self._requires.get(node, set()))

    def ready(self, completed: set[str]) -> tuple[str, ...]:
        return tuple(
            sorted(
                node
                for node, requirements in self._requires.items()
                if node not in completed and requirements.issubset(completed)
            )
        )

    def topological_order(self) -> tuple[str, ...]:
        indegree = {node: len(requirements) for node, requirements in self._requires.items()}
        dependents: dict[str, set[str]] = defaultdict(set)
        for node, requirements in self._requires.items():
            for requirement in requirements:
                dependents[requirement].add(node)

        queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
        ordered: list[str] = []
        while queue:
            current = queue.popleft()
            ordered.append(current)
            for dependent in sorted(dependents[current]):
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    queue.append(dependent)

        if len(ordered) != len(indegree):
            raise ValueError("dependency graph contains a cycle")
        return tuple(ordered)
