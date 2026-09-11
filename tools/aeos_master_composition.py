#!/usr/bin/env python3
"""Fail-closed composition boundary between execution and owner authority.

Execution results are evidence of execution only. They become owner-authority
readiness only when an externally produced trust proof is present, identity-bound,
and accepted by the existing Authority Packet and Pre-Authority contracts.
This module never executes controls, manufactures proof, approves, or merges.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from tools.aeos_authority_packet import AuthorityPacket as OwnerAuthorityPacket
from tools.aeos_authority_packet import packet_digest as authority_packet_digest
from tools.aeos_pre_authority_gate import AuthorityPacket as PreAuthorityPacket
from tools.aeos_pre_authority_gate import pre_authority_decision

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
EVIDENCE_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class MasterAssuranceSnapshot:
    iteration_id: str
    source_sha: str
    result_digest: str
    evidence_ids: tuple[str, ...]
    wave_results: tuple[tuple[str, str], ...]
    execution_manifest_digest: str

    def validate(self) -> None:
        if not self.iteration_id:
            raise ValueError("snapshot_iteration_missing")
        if not SHA_RE.fullmatch(self.source_sha):
            raise ValueError("snapshot_source_sha_invalid")
        if not self.result_digest or not re.fullmatch(r"[0-9a-f]{64}", self.result_digest):
            raise ValueError("snapshot_result_digest_invalid")
        if not self.execution_manifest_digest or not re.fullmatch(r"[0-9a-f]{64}", self.execution_manifest_digest):
            raise ValueError("snapshot_manifest_digest_invalid")
        if not self.evidence_ids or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("snapshot_evidence_ids_invalid")
        if any(not EVIDENCE_RE.fullmatch(item) for item in self.evidence_ids):
            raise ValueError("snapshot_evidence_id_invalid")
        if not self.wave_results:
            raise ValueError("snapshot_wave_results_missing")


@dataclass(frozen=True)
class MasterAssuranceComposition:
    snapshot: MasterAssuranceSnapshot
    authority_packet_digest: str
    pre_authority_digest: str
    decision: str
    reason: str

    def canonical(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "snapshot": {
                "iteration_id": self.snapshot.iteration_id,
                "source_sha": self.snapshot.source_sha,
                "result_digest": self.snapshot.result_digest,
                "evidence_ids": list(self.snapshot.evidence_ids),
                "wave_results": [list(item) for item in self.snapshot.wave_results],
                "execution_manifest_digest": self.snapshot.execution_manifest_digest,
            },
            "authority_packet_digest": self.authority_packet_digest,
            "pre_authority_digest": self.pre_authority_digest,
            "decision": self.decision,
            "reason": self.reason,
        }

    def digest(self) -> str:
        raw = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _tuple_strings(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"proof_{field}_invalid")
    return tuple(value)


def _owner_packet(payload: Mapping[str, Any]) -> OwnerAuthorityPacket:
    fields = {
        "original_change", "original_failure", "root_cause", "root_cause_proof",
        "fix_attempts", "final_fix", "failed_controls_history", "resolved_failures",
        "new_regressions", "exact_sha", "provenance", "evidence_integrity",
        "forensic_result", "independent_review", "remaining_risks",
        "remaining_assumptions", "assurance_debt", "recommended_decision",
    }
    missing = sorted(fields - set(payload))
    if missing:
        raise ValueError(f"proof_authority_packet_fields_missing:{','.join(missing)}")
    return OwnerAuthorityPacket(
        original_change=str(payload["original_change"]),
        original_failure=str(payload["original_failure"]),
        root_cause=str(payload["root_cause"]),
        root_cause_proof=_tuple_strings(payload["root_cause_proof"], "root_cause_proof"),
        fix_attempts=_tuple_strings(payload["fix_attempts"], "fix_attempts"),
        final_fix=str(payload["final_fix"]),
        failed_controls_history=_tuple_strings(payload["failed_controls_history"], "failed_controls_history"),
        resolved_failures=_tuple_strings(payload["resolved_failures"], "resolved_failures"),
        new_regressions=_tuple_strings(payload["new_regressions"], "new_regressions"),
        exact_sha=str(payload["exact_sha"]),
        provenance=_tuple_strings(payload["provenance"], "provenance"),
        evidence_integrity=_tuple_strings(payload["evidence_integrity"], "evidence_integrity"),
        forensic_result=str(payload["forensic_result"]),
        independent_review=str(payload["independent_review"]),
        remaining_risks=_tuple_strings(payload["remaining_risks"], "remaining_risks"),
        remaining_assumptions=_tuple_strings(payload["remaining_assumptions"], "remaining_assumptions"),
        assurance_debt=_tuple_strings(payload["assurance_debt"], "assurance_debt"),
        recommended_decision=str(payload["recommended_decision"]),
    )


def _pre_authority_packet(payload: Mapping[str, Any]) -> PreAuthorityPacket:
    required = {
        "gate_id", "iteration_id", "source_sha", "required_waves", "wave_results",
        "holds", "evidence_ids", "provenance_verified", "evidence_integrity_verified",
        "scope_verified", "root_cause_verified", "independent_review_verified",
        "assurance_self_check_verified", "remaining_risks", "remaining_assumptions",
        "assurance_debt",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"proof_pre_authority_fields_missing:{','.join(missing)}")
    wave_results = payload["wave_results"]
    if not isinstance(wave_results, (list, tuple)) or any(
        not isinstance(item, (list, tuple)) or len(item) != 2 or not all(isinstance(x, str) for x in item)
        for item in wave_results
    ):
        raise ValueError("proof_wave_results_invalid")
    return PreAuthorityPacket(
        gate_id=str(payload["gate_id"]),
        iteration_id=str(payload["iteration_id"]),
        source_sha=str(payload["source_sha"]),
        required_waves=_tuple_strings(payload["required_waves"], "required_waves"),
        wave_results=tuple((str(item[0]), str(item[1])) for item in wave_results),
        holds=_tuple_strings(payload["holds"], "holds"),
        evidence_ids=_tuple_strings(payload["evidence_ids"], "evidence_ids"),
        provenance_verified=bool(payload["provenance_verified"]),
        evidence_integrity_verified=bool(payload["evidence_integrity_verified"]),
        scope_verified=bool(payload["scope_verified"]),
        root_cause_verified=bool(payload["root_cause_verified"]),
        independent_review_verified=bool(payload["independent_review_verified"]),
        assurance_self_check_verified=bool(payload["assurance_self_check_verified"]),
        remaining_risks=_tuple_strings(payload["remaining_risks"], "remaining_risks"),
        remaining_assumptions=_tuple_strings(payload["remaining_assumptions"], "remaining_assumptions"),
        assurance_debt=_tuple_strings(payload["assurance_debt"], "assurance_debt"),
    )


def _result_digest(results: Sequence[Mapping[str, Any]]) -> str:
    raw = json.dumps(list(results), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compose_master_assurance(
    *,
    snapshot: MasterAssuranceSnapshot,
    proof: Mapping[str, Any] | None,
) -> MasterAssuranceComposition:
    """Compose independently produced proof; fail closed when it is absent."""
    snapshot.validate()
    if proof is None:
        return MasterAssuranceComposition(snapshot, "", "", "HOLD", "assurance_proof_missing")

    owner_payload = proof.get("authority_packet")
    pre_payload = proof.get("pre_authority_packet")
    if not isinstance(owner_payload, Mapping) or not isinstance(pre_payload, Mapping):
        return MasterAssuranceComposition(snapshot, "", "", "HOLD", "assurance_proof_incomplete")

    try:
        owner_packet = _owner_packet(owner_payload)
        owner_packet.validate()
        pre_packet = _pre_authority_packet(pre_payload)
        pre_decision = pre_authority_decision(pre_packet)
        owner_digest = authority_packet_digest(owner_packet)
        pre_digest = hashlib.sha256(
            json.dumps({
                "gate_id": pre_packet.gate_id,
                "iteration_id": pre_packet.iteration_id,
                "source_sha": pre_packet.source_sha,
                "decision": pre_decision,
            }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    except (TypeError, ValueError, KeyError) as exc:
        return MasterAssuranceComposition(snapshot, "", "", "HOLD", f"assurance_proof_invalid:{exc}")

    if owner_packet.exact_sha != snapshot.source_sha:
        return MasterAssuranceComposition(snapshot, owner_digest, pre_digest, "HOLD", "authority_packet_source_sha_mismatch")
    if pre_packet.source_sha != snapshot.source_sha:
        return MasterAssuranceComposition(snapshot, owner_digest, pre_digest, "HOLD", "pre_authority_source_sha_mismatch")
    if pre_packet.iteration_id != snapshot.iteration_id:
        return MasterAssuranceComposition(snapshot, owner_digest, pre_digest, "HOLD", "pre_authority_iteration_mismatch")
    if tuple(pre_packet.evidence_ids) != snapshot.evidence_ids:
        return MasterAssuranceComposition(snapshot, owner_digest, pre_digest, "HOLD", "pre_authority_evidence_mismatch")
    if pre_decision != "READY_FOR_AUTHORITY":
        return MasterAssuranceComposition(snapshot, owner_digest, pre_digest, "HOLD", f"pre_authority:{pre_decision}")
    if owner_packet.recommended_decision != "APPROVE":
        return MasterAssuranceComposition(snapshot, owner_digest, pre_digest, "HOLD", "authority_recommendation_not_approve")
    if owner_packet.independent_review != "PASS" or owner_packet.forensic_result != "PASS":
        return MasterAssuranceComposition(snapshot, owner_digest, pre_digest, "HOLD", "required_review_or_forensic_not_pass")

    return MasterAssuranceComposition(snapshot, owner_digest, pre_digest, "READY_FOR_OWNER_AUTHORITY", "assurance_composition_verified")


def snapshot_from_results(
    *,
    iteration_id: str,
    source_sha: str,
    results: Sequence[Any],
    execution_manifest_digest: str,
) -> MasterAssuranceSnapshot:
    rows = [
        {
            "set_id": result.set_id,
            "wave": result.wave,
            "state": result.state,
            "returncode": result.returncode,
            "command": result.command,
            "cwd": result.cwd,
            "duration_seconds": result.duration_seconds,
            "source_sha": result.source_sha,
            "iteration_id": result.iteration_id,
            "evidence_id": result.evidence_id,
            "detail": result.detail,
        }
        for result in results
    ]
    ordered = sorted(rows, key=lambda row: row["set_id"])
    evidence_ids = tuple(row["evidence_id"] for row in ordered)
    wave_results = tuple((row["set_id"], row["state"]) for row in ordered)
    snapshot = MasterAssuranceSnapshot(
        iteration_id=iteration_id,
        source_sha=source_sha,
        result_digest=_result_digest(ordered),
        evidence_ids=evidence_ids,
        wave_results=wave_results,
        execution_manifest_digest=execution_manifest_digest,
    )
    snapshot.validate()
    return snapshot


def load_proof(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("assurance_proof_root_invalid")
    return payload
