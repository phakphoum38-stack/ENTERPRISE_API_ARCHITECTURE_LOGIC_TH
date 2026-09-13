"""Open-ended AEOS Assurance Fabric primitives.

The fabric is a registry/compiler boundary, not a self-certifying authority.
It lets new universes, planes, domains and controls be declared without a
hard-coded maximum while preserving immutable trust rules.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


class AssuranceFabricError(ValueError):
    """Raised for invalid assurance model extensions."""


_FORBIDDEN = {"PASS", "CERTIFIED", "AUTHORIZED"}


@dataclass(frozen=True)
class AssuranceControl:
    control_id: str
    universe: str
    plane: str
    domain: str
    risk: str
    scope: str
    evidence_requirements: tuple[str, ...]
    verification_modes: tuple[str, ...]
    failure_state: str
    recovery_strategy: str

    def __post_init__(self) -> None:
        for name in ("control_id", "universe", "plane", "domain", "risk", "scope", "failure_state", "recovery_strategy"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name):
                raise AssuranceFabricError(f"{name} required")
        for name in ("evidence_requirements", "verification_modes"):
            value = getattr(self, name)
            if not isinstance(value, tuple) or not value or len(set(value)) != len(value) or any(not isinstance(x, str) or not x for x in value):
                raise AssuranceFabricError(f"{name} must be a unique nonempty tuple")
        if self.failure_state in _FORBIDDEN:
            raise AssuranceFabricError("failure_state cannot assert certification")


class AssuranceFabric:
    """Deterministic in-memory registry; persistence is an external adapter."""

    def __init__(self) -> None:
        self._controls: dict[str, AssuranceControl] = {}

    def register(self, control: AssuranceControl) -> None:
        if control.control_id in self._controls:
            raise AssuranceFabricError("duplicate control_id")
        self._controls[control.control_id] = control

    def get(self, control_id: str) -> AssuranceControl:
        try:
            return self._controls[control_id]
        except KeyError as exc:
            raise AssuranceFabricError("unknown control") from exc

    def ordered(self) -> tuple[AssuranceControl, ...]:
        return tuple(self._controls[key] for key in sorted(self._controls))

    def coverage(self) -> dict[str, int]:
        controls = self.ordered()
        return {
            "universes": len({c.universe for c in controls}),
            "planes": len({c.plane for c in controls}),
            "domains": len({c.domain for c in controls}),
            "controls": len(controls),
        }


def compile_control_spec(spec: Mapping[str, object]) -> AssuranceControl:
    """Compile one declarative control without certifying its implementation."""
    if not isinstance(spec, Mapping):
        raise AssuranceFabricError("control specification must be a mapping")
    required = ("control_id", "universe", "plane", "domain", "risk", "scope", "evidence_requirements", "verification_modes", "failure_state", "recovery_strategy")
    missing = [key for key in required if key not in spec]
    if missing:
        raise AssuranceFabricError(f"missing control fields: {','.join(missing)}")
    return AssuranceControl(
        control_id=spec["control_id"], universe=spec["universe"], plane=spec["plane"], domain=spec["domain"], risk=spec["risk"], scope=spec["scope"],
        evidence_requirements=tuple(spec["evidence_requirements"]), verification_modes=tuple(spec["verification_modes"]),
        failure_state=spec["failure_state"], recovery_strategy=spec["recovery_strategy"],
    )
