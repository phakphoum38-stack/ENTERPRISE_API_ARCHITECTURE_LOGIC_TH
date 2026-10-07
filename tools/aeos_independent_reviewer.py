#!/usr/bin/env python3
"""Deterministic AEOS protocol-level Independent Technical Reviewer.

This actor is REVIEW_ONLY. It evaluates a supplied evidence bundle against the
canonical review contract and emits a decision. It does not impersonate a
GitHub reviewer, grant Owner Authority, approve, or merge.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ACTOR_ID = "AEOS-INDEPENDENT-REVIEWER-001"
AUTHORITY = "REVIEW_ONLY"


class IndependentReviewError(ValueError):
    """Raised when the independent-review evidence bundle is unsafe."""


@dataclass(frozen=True)
class ReviewEvidence:
    repository: str
    pull_request: int
    base_sha: str
    head_sha: str
    protected_baseline: str
    changed_files: tuple[str, ...]
    ci_pass: bool
    forensic_pass: bool
    tests_pass: bool
    provenance_pass: bool
    scope_pass: bool
    authority_boundary_pass: bool
    source_identity_pass: bool
    root_cause_verified: bool

    def validate(self) -> None:
        if not self.repository or self.pull_request <= 0:
            raise IndependentReviewError("REVIEW_TARGET_INVALID")
        for name, value in (
            ("base_sha", self.base_sha),
            ("head_sha", self.head_sha),
            ("protected_baseline", self.protected_baseline),
        ):
            if not SHA_RE.fullmatch(value):
                raise IndependentReviewError(f"INVALID_{name.upper()}")
        if self.base_sha == self.head_sha:
            raise IndependentReviewError("NO_CHANGE_TO_REVIEW")
        if not self.changed_files:
            raise IndependentReviewError("REVIEW_SCOPE_EMPTY")
        if any(not path or path.startswith("/") for path in self.changed_files):
            raise IndependentReviewError("INVALID_REVIEW_SCOPE")


@dataclass(frozen=True)
class IndependentReview:
    actor: str
    authority: str
    mode: str
    target_sha: str
    decision: str
    recommendation: str
    findings: tuple[str, ...]
    evidence_digest: str
    owner_authority: str
    merge_authorization: str

    def canonical(self) -> dict[str, object]:
        return {
            "review_actor": self.actor,
            "authority": self.authority,
            "review_mode": self.mode,
            "target_sha": self.target_sha,
            "decision": self.decision,
            "recommendation": self.recommendation,
            "findings": list(self.findings),
            "evidence_digest": self.evidence_digest,
            "owner_authority": self.owner_authority,
            "merge_authorization": self.merge_authorization,
        }


def _digest(evidence: ReviewEvidence) -> str:
    payload = json.dumps(evidence.__dict__, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def perform_independent_review(evidence: ReviewEvidence) -> IndependentReview:
    """Evaluate evidence independently and fail closed on any failed control."""
    evidence.validate()
    checks = {
        "CI": evidence.ci_pass,
        "FORENSIC": evidence.forensic_pass,
        "TESTS": evidence.tests_pass,
        "PROVENANCE": evidence.provenance_pass,
        "SCOPE": evidence.scope_pass,
        "AUTHORITY_BOUNDARY": evidence.authority_boundary_pass,
        "SOURCE_IDENTITY": evidence.source_identity_pass,
        "ROOT_CAUSE": evidence.root_cause_verified,
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    decision = "PASS" if not failed else "HOLD"
    recommendation = "PROCEED TO PRE-AUTHORITY" if decision == "PASS" else "HARD_STOP"
    return IndependentReview(
        actor=ACTOR_ID,
        authority=AUTHORITY,
        mode="External Technical Review",
        target_sha=evidence.head_sha,
        decision=decision,
        recommendation=recommendation,
        findings=failed,
        evidence_digest=_digest(evidence),
        owner_authority="NOT GRANTED",
        merge_authorization="LOCKED",
    )


if __name__ == "__main__":
    print("AEOS_INDEPENDENT_REVIEWER=READY")
