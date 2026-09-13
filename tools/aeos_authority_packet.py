#!/usr/bin/env python3
"""Build a fail-closed Owner Authority Packet.

The packet is an evidence package, not an authority action. Autobot may
prepare and recommend; it may never approve or merge.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class AuthorityPacket:
    original_change: str
    original_failure: str
    root_cause: str
    root_cause_proof: tuple[str, ...]
    fix_attempts: tuple[str, ...]
    final_fix: str
    failed_controls_history: tuple[str, ...]
    resolved_failures: tuple[str, ...]
    new_regressions: tuple[str, ...]
    exact_sha: str
    provenance: tuple[str, ...]
    evidence_integrity: tuple[str, ...]
    forensic_result: str
    independent_review: str
    remaining_risks: tuple[str, ...]
    remaining_assumptions: tuple[str, ...]
    assurance_debt: tuple[str, ...]
    recommended_decision: str

    def validate(self) -> None:
        required_text = (
            self.original_change, self.original_failure, self.root_cause,
            self.final_fix, self.forensic_result, self.independent_review,
            self.recommended_decision,
        )
        if any(not item for item in required_text):
            raise ValueError("authority_packet_required_field_missing")
        if not SHA_RE.fullmatch(self.exact_sha):
            raise ValueError("invalid_exact_sha")
        for evidence in self.root_cause_proof:
            if not EVIDENCE_RE.fullmatch(evidence):
                raise ValueError("invalid_root_cause_evidence_id")
        if not self.root_cause_proof:
            raise ValueError("root_cause_proof_missing")
        if not self.fix_attempts:
            raise ValueError("fix_attempt_history_missing")
        if not self.provenance:
            raise ValueError("provenance_missing")
        if not self.evidence_integrity:
            raise ValueError("evidence_integrity_missing")
        if self.forensic_result != "PASS":
            raise ValueError("forensic_not_pass")
        if self.independent_review != "PASS":
            raise ValueError("independent_review_not_pass")
        if self.recommended_decision not in {"APPROVE", "REJECT", "HOLD"}:
            raise ValueError("invalid_recommended_decision")

    def canonical(self) -> dict[str, object]:
        self.validate()
        return {
            "schema_version": "1.0",
            "contract": "AEOS_AUTHORITY_PACKET",
            "original_change": self.original_change,
            "original_failure": self.original_failure,
            "root_cause": self.root_cause,
            "root_cause_proof": list(self.root_cause_proof),
            "fix_attempts": list(self.fix_attempts),
            "final_fix": self.final_fix,
            "failed_controls_history": list(self.failed_controls_history),
            "resolved_failures": list(self.resolved_failures),
            "new_regressions": list(self.new_regressions),
            "exact_sha": self.exact_sha,
            "provenance": list(self.provenance),
            "evidence_integrity": list(self.evidence_integrity),
            "forensic_result": self.forensic_result,
            "independent_review": self.independent_review,
            "remaining_risks": list(self.remaining_risks),
            "remaining_assumptions": list(self.remaining_assumptions),
            "assurance_debt": list(self.assurance_debt),
            "recommended_decision": self.recommended_decision,
            "authority_boundary": {
                "autobot_may_prepare": True,
                "autobot_may_recommend": True,
                "autobot_may_approve": False,
                "autobot_may_merge": False,
            },
        }


def packet_digest(packet: AuthorityPacket) -> str:
    payload = json.dumps(packet.canonical(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    print("AEOS_AUTHORITY_PACKET=READY")
