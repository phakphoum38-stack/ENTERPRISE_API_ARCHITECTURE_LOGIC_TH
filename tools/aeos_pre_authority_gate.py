#!/usr/bin/env python3
"""Fail-closed Pre-Authority gate for AEOS Autobot.

This gate reconciles wave, hold, provenance, evidence, scope, root-cause,
independent-review, and self-integrity assertions. It prepares authority
readiness only; it cannot approve or merge.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class AuthorityPacket:
    gate_id: str
    iteration_id: str
    source_sha: str
    required_waves: tuple[str, ...]
    wave_results: tuple[tuple[str, str], ...]
    holds: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    provenance_verified: bool
    evidence_integrity_verified: bool
    scope_verified: bool
    root_cause_verified: bool
    independent_review_verified: bool
    assurance_self_check_verified: bool
    remaining_risks: tuple[str, ...]
    remaining_assumptions: tuple[str, ...]
    assurance_debt: tuple[str, ...]

    def validate_identity(self) -> None:
        if not self.gate_id or not self.iteration_id:
            raise ValueError("gate_identity_missing")
        if not SHA_RE.fullmatch(self.source_sha):
            raise ValueError("invalid_source_sha")
        if not self.required_waves or len(set(self.required_waves)) != len(self.required_waves):
            raise ValueError("invalid_required_waves")
        if any(not EVIDENCE_RE.fullmatch(item) for item in self.evidence_ids):
            raise ValueError("invalid_evidence_id")
        if len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("duplicate_evidence_id")

    def decision(self) -> str:
        self.validate_identity()
        if not self.wave_results:
            return "BLOCKED"
        expected = set(self.required_waves)
        observed = {wave for wave, _ in self.wave_results}
        if observed != expected:
            return "HOLD"
        if any(result != "PASS" for _, result in self.wave_results):
            return "HOLD"
        if self.holds:
            return "HOLD"
        checks = (
            self.provenance_verified,
            self.evidence_integrity_verified,
            self.scope_verified,
            self.root_cause_verified,
            self.independent_review_verified,
            self.assurance_self_check_verified,
        )
        if not all(checks):
            return "BLOCKED"
        return "READY_FOR_AUTHORITY"


def packet_digest(packet: AuthorityPacket) -> str:
    packet.validate_identity()
    payload = "|".join((
        packet.gate_id,
        packet.iteration_id,
        packet.source_sha,
        ",".join(packet.required_waves),
        ",".join(f"{wave}:{result}" for wave, result in packet.wave_results),
        ",".join(packet.holds),
        ",".join(packet.evidence_ids),
        str(packet.provenance_verified),
        str(packet.evidence_integrity_verified),
        str(packet.scope_verified),
        str(packet.root_cause_verified),
        str(packet.independent_review_verified),
        str(packet.assurance_self_check_verified),
        ",".join(packet.remaining_risks),
        ",".join(packet.remaining_assumptions),
        ",".join(packet.assurance_debt),
    ))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def pre_authority_decision(packet: AuthorityPacket) -> str:
    return packet.decision()


if __name__ == "__main__":
    print("AEOS_PRE_AUTHORITY_GATE=READY")
