from __future__ import annotations

from dataclasses import dataclass
from itertools import product
import hashlib
import json
from typing import Mapping, Sequence

@dataclass(frozen=True)
class ScenarioDimension:
    name: str
    values: tuple[str, ...]

class ScenarioAlgebraError(ValueError):
    pass

class ScenarioAlgebra:
    """Bounded logical Cartesian-product algebra; never materializes the full space."""
    def __init__(self, dimensions: Sequence[ScenarioDimension]):
        names = [d.name for d in dimensions]
        if not dimensions: raise ScenarioAlgebraError("at least one dimension is required")
        if len(names) != len(set(names)): raise ScenarioAlgebraError("duplicate dimension name")
        for d in dimensions:
            if not d.values: raise ScenarioAlgebraError(f"empty dimension: {d.name}")
            if len(set(d.values)) != len(d.values): raise ScenarioAlgebraError(f"duplicate value: {d.name}")
        self._dimensions = tuple(dimensions)
    @property
    def cardinality(self) -> int:
        total = 1
        for d in self._dimensions: total *= len(d.values)
        return total
    def validate(self, scenario: Mapping[str, str]) -> None:
        expected = {d.name for d in self._dimensions}
        if set(scenario) != expected:
            raise ScenarioAlgebraError(f"dimension mismatch: missing={sorted(expected-set(scenario))}; extra={sorted(set(scenario)-expected)}")
        for d in self._dimensions:
            if scenario[d.name] not in d.values: raise ScenarioAlgebraError(f"invalid value for {d.name}: {scenario[d.name]!r}")
    def canonicalize(self, scenario: Mapping[str, str]) -> tuple[tuple[str, str], ...]:
        self.validate(scenario)
        return tuple((d.name, scenario[d.name]) for d in self._dimensions)
    def scenario_id(self, scenario: Mapping[str, str]) -> str:
        payload = json.dumps(self.canonicalize(scenario), separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(payload.encode()).hexdigest()
    def sample(self, limit: int) -> list[dict[str, str]]:
        if limit < 1: raise ScenarioAlgebraError("sample limit must be positive")
        result=[]
        names=[d.name for d in self._dimensions]
        for combo in product(*(d.values for d in self._dimensions)):
            if len(result) >= limit: break
            result.append(dict(zip(names, combo)))
        return result
