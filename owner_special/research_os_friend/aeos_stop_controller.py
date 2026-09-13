"""Authoritative AEOS stop-proof boundary.

Only a VerifiedCompletionObservation may reach the stop-proof projection.
This prevents direct caller-supplied counters/flags from being treated as an
independent completion decision.
"""
from __future__ import annotations

from typing import Any

from .aeos_completion_verifier import VerifiedCompletionObservation
from .autonomous_workloop import build_stop_proof


def build_authoritative_stop_proof(
    observation: VerifiedCompletionObservation,
) -> dict[str, Any]:
    """Project a stop proof from an independently verified observation."""
    if not isinstance(observation, VerifiedCompletionObservation) or not observation.verified:
        raise TypeError("stop proof requires a verified completion observation")

    proof = build_stop_proof(**observation.observations)
    proof["observation_schema"] = "research-os-aeos-completion-observation/v1"
    proof["baseline_sha"] = observation.baseline_sha
    proof["scan_order"] = list(observation.scan_order)
    proof["evidence_digest"] = observation.evidence_digest
    proof["independently_verified"] = True
    return proof
