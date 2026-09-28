"""Integrated AEOS assurance boundary.

This module composes reality, freshness, independence and negative-space
observations before the independent completion verifier is allowed to create a
verified completion observation. It is intentionally an adapter/orchestrator:
it does not manufacture evidence, authority, or certification.
"""
from __future__ import annotations

from typing import Any, Mapping

from .aeos_anti_circularity import IndependenceDecision
from .aeos_completion_verifier import VerifiedCompletionObservation, verify_completion_observation
from .aeos_negative_space import NegativeSpaceReport
from .aeos_reality_boundary import RealityObservation
from .aeos_temporal_freshness import FreshnessDecision


class AssuranceBoundaryError(ValueError):
    """Raised when prerequisite assurance observations are not admissible."""


def build_verified_completion_observation(
    *,
    reality: RealityObservation,
    freshness: FreshnessDecision,
    independence: IndependenceDecision,
    negative_space: NegativeSpaceReport,
    scan_results: Mapping[str, Any],
    evidence_refs: tuple[str, ...],
) -> VerifiedCompletionObservation:
    """Compose admissible observations and delegate final verification.

    Reality must be valid and fresh, the verifier/source relationship must be
    independent, and the negative-space scan must pass. The function does not
    turn any of those observations into truth on its own; the dedicated
    completion verifier remains the final construction boundary.
    """
    if reality.status != "VALID":
        raise AssuranceBoundaryError("reality observation is not valid")
    if reality.baseline_sha != reality.observed_sha:
        raise AssuranceBoundaryError("reality observation is stale")
    if not freshness.fresh or freshness.status != "FRESH":
        raise AssuranceBoundaryError(f"reality observation is {freshness.status}")
    if not independence.independent:
        raise AssuranceBoundaryError("completion verification source is not independent")
    if not negative_space.passed:
        raise AssuranceBoundaryError("negative-space scan did not pass")
    if type(evidence_refs) is not tuple or not evidence_refs:
        raise AssuranceBoundaryError("completion evidence references required")

    return verify_completion_observation(
        baseline_sha=reality.baseline_sha,
        observed_sha=reality.observed_sha,
        scan_results=scan_results,
        evidence_refs=evidence_refs,
    )
