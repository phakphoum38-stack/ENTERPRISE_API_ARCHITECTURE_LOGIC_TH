#!/usr/bin/env python3
"""Native Research OS Experience Studio.

Deterministic, bounded design-model kernel for the native Control Center.
It models visual tokens, components, states, motion, accessibility and
evidence without becoming a second runtime, scheduler or authority system.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any


class ExperienceState(str, Enum):
    PROPOSED = "PROPOSED"
    DESIGNED = "DESIGNED"
    IMPLEMENTED = "IMPLEMENTED"
    FUNCTIONALLY_VERIFIED = "FUNCTIONALLY_VERIFIED"
    VISUALLY_VERIFIED = "VISUALLY_VERIFIED"
    ACCESSIBILITY_VERIFIED = "ACCESSIBILITY_VERIFIED"
    EVIDENCED = "EVIDENCED"
    RELEASED = "RELEASED"
    MONITORED = "MONITORED"


class MotionMode(str, Enum):
    FULL = "FULL"
    REDUCED = "REDUCED"
    NONE = "NONE"


@dataclass(frozen=True)
class ColorToken:
    token: str
    role: str
    value: str
    contrast_ratio: float | None = None
    dark_value: str | None = None

    def validate(self) -> None:
        if not self.token or not self.role or not self.value:
            raise ValueError("color token identity, role and value are required")
        if self.contrast_ratio is not None and self.contrast_ratio < 0:
            raise ValueError("contrast ratio cannot be negative")


@dataclass(frozen=True)
class ComponentState:
    name: str
    motion: MotionMode = MotionMode.FULL
    interactive: bool = True
    description: str = ""


@dataclass(frozen=True)
class MotionSpec:
    transition_id: str
    from_state: str
    to_state: str
    duration_ms: int = 180
    reversible: bool = True
    reduced_motion_duration_ms: int = 0

    def validate(self) -> None:
        if not self.transition_id or not self.from_state or not self.to_state:
            raise ValueError("motion identity and endpoints are required")
        if self.duration_ms < 0 or self.reduced_motion_duration_ms < 0:
            raise ValueError("motion duration cannot be negative")


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    fingerprint: str
    kind: str

    def validate(self) -> None:
        if not self.evidence_id or not self.kind:
            raise ValueError("evidence identity and kind are required")
        if len(self.fingerprint) != 64:
            raise ValueError("evidence fingerprint must be SHA-256")


@dataclass
class Component:
    component_id: str
    name: str
    states: dict[str, ComponentState] = field(default_factory=dict)
    motions: list[MotionSpec] = field(default_factory=list)
    evidence: list[EvidenceRef] = field(default_factory=list)
    state: ExperienceState = ExperienceState.PROPOSED

    def add_state(self, item: ComponentState) -> None:
        if not item.name:
            raise ValueError("component state name is required")
        if item.name in self.states:
            raise ValueError(f"duplicate component state: {item.name}")
        self.states[item.name] = item

    def add_motion(self, item: MotionSpec) -> None:
        item.validate()
        self.motions.append(item)

    def add_evidence(self, item: EvidenceRef) -> None:
        item.validate()
        self.evidence.append(item)

    def transition(self, state: ExperienceState) -> None:
        if state in {
            ExperienceState.FUNCTIONALLY_VERIFIED,
            ExperienceState.VISUALLY_VERIFIED,
            ExperienceState.ACCESSIBILITY_VERIFIED,
            ExperienceState.EVIDENCED,
            ExperienceState.RELEASED,
            ExperienceState.MONITORED,
        } and not self.evidence:
            raise ValueError("verification/release states require evidence")
        self.state = state


@dataclass
class ExperienceStudio:
    max_components: int = 1000
    colors: dict[str, ColorToken] = field(default_factory=dict)
    components: dict[str, Component] = field(default_factory=dict)

    def add_color(self, token: ColorToken) -> None:
        token.validate()
        if token.token in self.colors:
            raise ValueError(f"duplicate color token: {token.token}")
        self.colors[token.token] = token

    def add_component(self, component: Component) -> None:
        if not component.component_id or not component.name:
            raise ValueError("component identity and name are required")
        if component.component_id in self.components:
            raise ValueError(f"duplicate component: {component.component_id}")
        if len(self.components) >= self.max_components:
            raise RuntimeError("component bound exceeded")
        self.components[component.component_id] = component

    def audit(self) -> dict[str, Any]:
        issues: list[str] = []
        for token in self.colors.values():
            if token.contrast_ratio is not None and token.contrast_ratio < 4.5:
                issues.append(f"low_contrast:{token.token}")
        for component in self.components.values():
            required = {"default", "loading", "empty", "error", "offline", "recovery"}
            missing = sorted(required - set(component.states))
            if missing:
                issues.append(f"missing_states:{component.component_id}:{','.join(missing)}")
            for motion in component.motions:
                motion.validate()
        return {
            "status": "PASS" if not issues else "HOLD",
            "issues": issues,
            "components": len(self.components),
            "colors": len(self.colors),
        }

    def render_model(self) -> dict[str, Any]:
        return {
            "colors": {
                k: {
                    "role": v.role,
                    "value": v.value,
                    "dark_value": v.dark_value,
                    "contrast_ratio": v.contrast_ratio,
                }
                for k, v in sorted(self.colors.items())
            },
            "components": {
                k: {
                    "name": v.name,
                    "state": v.state.value,
                    "states": sorted(v.states),
                    "motions": [
                        {
                            "id": m.transition_id,
                            "from": m.from_state,
                            "to": m.to_state,
                            "duration_ms": m.duration_ms,
                            "reduced_motion_duration_ms": m.reduced_motion_duration_ms,
                            "reversible": m.reversible,
                        }
                        for m in v.motions
                    ],
                }
                for k, v in sorted(self.components.items())
            },
        }

    def fingerprint(self) -> str:
        payload = json.dumps(self.render_model(), sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode("utf-8")).hexdigest()
