"""Fail-closed runtime readiness state machine for the Research OS Platform.

Validation-only boundary: it observes/records readiness transitions but never
starts processes, schedules work, authorizes execution, releases resources, or
becomes a second runtime.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

STATES = (
    "PROCESS_START",
    "DEPENDENCY_READY",
    "IMPORT_READY",
    "LISTENER_READY",
    "HEALTH_OK",
    "READY",
)
_ALLOWED = {
    "PROCESS_START": {"DEPENDENCY_READY"},
    "DEPENDENCY_READY": {"IMPORT_READY"},
    "IMPORT_READY": {"LISTENER_READY"},
    "LISTENER_READY": {"HEALTH_OK"},
    "HEALTH_OK": {"READY"},
    "READY": set(),
}


@dataclass(frozen=True)
class ReadinessEvidence:
    state: str
    source_sha: str
    correlation_id: str
    result: str = "PASS"

    def to_dict(self) -> dict[str, str]:
        return {
            "state": self.state,
            "source_sha": self.source_sha,
            "correlation_id": self.correlation_id,
            "result": self.result,
        }


@dataclass
class RuntimeReadiness:
    source_sha: str
    correlation_id: str
    state: str = "PROCESS_START"

    def advance(self, next_state: str) -> ReadinessEvidence:
        if next_state not in STATES:
            raise ValueError("unknown readiness state")
        if next_state not in _ALLOWED[self.state]:
            raise ValueError(
                f"invalid readiness transition: {self.state} -> {next_state}"
            )
        self.state = next_state
        return ReadinessEvidence(
            state=next_state,
            source_sha=self.source_sha,
            correlation_id=self.correlation_id,
        )

    def require_ready(self) -> None:
        if self.state != "READY":
            raise RuntimeError(f"runtime is not READY: {self.state}")


def validate_readiness_sequence(states: list[str]) -> tuple[str, ...]:
    failures: list[str] = []
    if not states:
        return ("empty_readiness_sequence",)
    if states[0] != "PROCESS_START":
        failures.append("sequence_must_start_with_PROCESS_START")
    current = "PROCESS_START"
    for state in states[1:]:
        if state not in STATES:
            failures.append(f"unknown_state:{state}")
            continue
        if state not in _ALLOWED[current]:
            failures.append(f"invalid_transition:{current}->{state}")
        current = state
    if current != "READY":
        failures.append("sequence_must_end_with_READY")
    return tuple(failures)


def build_readiness_evidence(
    *,
    source_sha: str,
    correlation_id: str,
    states: list[str],
) -> list[dict[str, Any]]:
    failures = validate_readiness_sequence(states)
    if failures:
        raise ValueError("readiness validation failed: " + "; ".join(failures))
    return [
        ReadinessEvidence(
            state=state,
            source_sha=source_sha,
            correlation_id=correlation_id,
        ).to_dict()
        for state in states
    ]


__all__ = [
    "STATES",
    "ReadinessEvidence",
    "RuntimeReadiness",
    "build_readiness_evidence",
    "validate_readiness_sequence",
]
