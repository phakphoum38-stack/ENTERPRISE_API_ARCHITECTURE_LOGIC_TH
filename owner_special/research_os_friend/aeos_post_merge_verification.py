"""Post-merge verification boundary for AEOS.

The verifier consumes independently observed post-merge state. It never
performs the merge and never treats merge success as proof of health.
"""
from __future__ import annotations

from dataclasses import dataclass


class PostMergeVerificationError(ValueError):
    """Raised when post-merge state is unsafe or incomplete."""


@dataclass(frozen=True)
class PostMergeObservation:
    expected_main_sha: str
    observed_main_sha: str
    ci_passed: bool
    runtime_healthy: bool
    evidence_refs: tuple[str, ...]
    verified: bool = True

    def __post_init__(self) -> None:
        for value, name in ((self.expected_main_sha, "expected_main_sha"), (self.observed_main_sha, "observed_main_sha")):
            if not isinstance(value, str) or len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
                raise PostMergeVerificationError(f"invalid {name}")
        if self.expected_main_sha != self.observed_main_sha:
            raise PostMergeVerificationError("post-merge main SHA mismatch")
        for value, name in ((self.ci_passed, "ci_passed"), (self.runtime_healthy, "runtime_healthy"), (self.verified, "verified")):
            if type(value) is not bool:
                raise PostMergeVerificationError(f"{name} must be boolean")
        if not self.ci_passed or not self.runtime_healthy or not self.verified:
            raise PostMergeVerificationError("post-merge verification failed")
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs or len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise PostMergeVerificationError("unique evidence_refs required")


def verify_post_merge(*, expected_main_sha: str, observed_main_sha: str, ci_passed: bool, runtime_healthy: bool, evidence_refs: tuple[str, ...]) -> PostMergeObservation:
    return PostMergeObservation(expected_main_sha, observed_main_sha, ci_passed, runtime_healthy, evidence_refs)
