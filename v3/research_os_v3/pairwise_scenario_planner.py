from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from v3.research_os_v3.scenario_algebra import ScenarioAlgebra, ScenarioDimension

@dataclass(frozen=True)
class BoundaryPair:
    left: str
    right: str

class PairwiseScenarioPlanner:
    """Produces bounded pairwise dimension/value coverage without full expansion."""
    def __init__(self, algebra: ScenarioAlgebra): self.algebra = algebra
    def dimension_pairs(self) -> tuple[BoundaryPair, ...]:
        return tuple(BoundaryPair(a.name,b.name) for a,b in combinations(self.algebra._dimensions,2))
    def boundary_values(self, dimension: ScenarioDimension) -> tuple[str,...]:
        return dimension.values if len(dimension.values)<=2 else (dimension.values[0],dimension.values[-1])
    def pairwise_scenarios(self, limit: int) -> list[dict[str,str]]:
        if limit < 1: raise ValueError("limit must be positive")
        names=[d.name for d in self.algebra._dimensions]
        domains=[self.boundary_values(d) for d in self.algebra._dimensions]
        result=[]; seen=set()
        import itertools
        for combo in itertools.product(*domains):
            scenario=dict(zip(names,combo)); sid=self.algebra.scenario_id(scenario)
            if sid not in seen:
                seen.add(sid); result.append(scenario)
            if len(result)>=limit: break
        return result