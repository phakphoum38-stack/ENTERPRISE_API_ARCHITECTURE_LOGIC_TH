"""Deterministic compiler for risk-selected AEOS assurance cases.

This module does not certify anything and does not observe repository state.
It converts a declarative assurance space into bounded, deterministic case
identifiers so concrete scanners/verifiers can select executable checks.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from itertools import product
from typing import Iterable


class AssuranceCompilerError(ValueError):
    pass


@dataclass(frozen=True)
class AssuranceCase:
    case_id: str
    domain: str
    dimension: str
    state: str
    risk: str
    actor: str
    mode: str


def _token(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise AssuranceCompilerError("assurance values must be non-empty strings")
    return value


def compile_assurance_cases(
    *,
    domains: Iterable[str],
    dimensions: Iterable[str],
    states: Iterable[str],
    risks: Iterable[str],
    actors: Iterable[str],
    modes: Iterable[str],
    max_cases: int = 10000,
) -> tuple[AssuranceCase, ...]:
    """Compile a bounded deterministic assurance universe.

    The compiler intentionally does not brute-force an unbounded universe.
    Callers choose bounded axes; ordering is canonicalized and case IDs are
    derived from all six dimensions.
    """
    if type(max_cases) is not int or max_cases <= 0:
        raise AssuranceCompilerError("max_cases must be a positive integer")

    axes = []
    for values in (domains, dimensions, states, risks, actors, modes):
        normalized = tuple(sorted({_token(v) for v in values}))
        if not normalized:
            raise AssuranceCompilerError("each assurance axis must be non-empty")
        axes.append(normalized)

    total = 1
    for axis in axes:
        total *= len(axis)
    if total > max_cases:
        raise AssuranceCompilerError(
            f"assurance universe exceeds bound: {total} > {max_cases}"
        )

    cases = []
    for values in product(*axes):
        domain, dimension, state, risk, actor, mode = values
        canonical = {
            "actor": actor,
            "dimension": dimension,
            "domain": domain,
            "mode": mode,
            "risk": risk,
            "state": state,
        }
        digest = hashlib.sha256(
            json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()[:16]
        cases.append(
            AssuranceCase(
                case_id=f"AC-{digest}",
                domain=domain,
                dimension=dimension,
                state=state,
                risk=risk,
                actor=actor,
                mode=mode,
            )
        )
    return tuple(cases)


def select_high_risk_cases(cases: Iterable[AssuranceCase]) -> tuple[AssuranceCase, ...]:
    """Select hard-risk cases without changing their canonical order."""
    selected = [
        case
        for case in cases
        if case.risk in {"HIGH", "CRITICAL", "IRREVERSIBLE", "SAFETY_CRITICAL", "SECURITY_CRITICAL", "GOVERNANCE_CRITICAL"}
    ]
    return tuple(sorted(selected, key=lambda case: case.case_id))
