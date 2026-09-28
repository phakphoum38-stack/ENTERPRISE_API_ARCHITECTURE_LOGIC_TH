#!/usr/bin/env python3
"""Prepare a fail-closed successor generation record.

This module records lineage and verifies the minimum evidence boundary for a
rebaseline. It does not certify, approve, merge, rewrite history, or mutate
refs. The caller remains responsible for authoritative verification and human
Owner authority where required.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Mapping

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class RebaselineInput:
    parent_sha: str
    successor_sha: str
    evidence_root: str
    provenance_root: str
    assurance_state: str
    known_risks: tuple[str, ...]
    lessons_learned: tuple[str, ...]
    immutability_verified: bool
    verification_complete: bool

    def validate(self) -> None:
        if not SHA_RE.fullmatch(self.parent_sha):
            raise ValueError("invalid_parent_sha")
        if not SHA_RE.fullmatch(self.successor_sha):
            raise ValueError("invalid_successor_sha")
        if not DIGEST_RE.fullmatch(self.evidence_root):
            raise ValueError("invalid_evidence_root")
        if not DIGEST_RE.fullmatch(self.provenance_root):
            raise ValueError("invalid_provenance_root")
        if self.parent_sha == self.successor_sha:
            raise ValueError("successor_must_differ_from_parent")
        if self.assurance_state not in {"VERIFIED", "ASSURED", "CERTIFIED"}:
            raise ValueError("successor_not_verified")
        if not self.immutability_verified:
            raise ValueError("parent_immutability_not_verified")
        if not self.verification_complete:
            raise ValueError("successor_verification_incomplete")


@dataclass(frozen=True)
class RebaselineRecord:
    parent_sha: str
    successor_sha: str
    evidence_root: str
    provenance_root: str
    assurance_state: str
    known_risks: tuple[str, ...]
    lessons_learned: tuple[str, ...]

    def canonical(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "contract": "RESEARCH_OS_REBASELINE",
            "state": "REBASELINE_RECORDED",
            "lineage": {
                "parent_generation_sha": self.parent_sha,
                "successor_generation_sha": self.successor_sha,
            },
            "evidence_root": self.evidence_root,
            "provenance_root": self.provenance_root,
            "assurance_state": self.assurance_state,
            "known_risks": list(self.known_risks),
            "lessons_learned": list(self.lessons_learned),
            "history_policy": {
                "parent_is_immutable": True,
                "prior_evidence_is_preserved": True,
                "certification_is_not_inherited": True,
            },
            "authority_boundary": {
                "prepares_record": True,
                "grants_authority": False,
                "approves_certification": False,
                "mutates_git_refs": False,
            },
        }


def prepare_rebaseline(data: RebaselineInput) -> RebaselineRecord:
    """Validate the boundary and return a deterministic successor record."""
    data.validate()
    return RebaselineRecord(
        parent_sha=data.parent_sha,
        successor_sha=data.successor_sha,
        evidence_root=data.evidence_root,
        provenance_root=data.provenance_root,
        assurance_state=data.assurance_state,
        known_risks=data.known_risks,
        lessons_learned=data.lessons_learned,
    )


def record_digest(record: RebaselineRecord) -> str:
    payload = json.dumps(record.canonical(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print("REBASELINE_ENGINE=READY")
