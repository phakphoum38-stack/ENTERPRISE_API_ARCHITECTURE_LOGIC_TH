#!/usr/bin/env python3
"""Verifier-issued, target-bound assurance proof for the AEOS master boundary."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_VERIFIER_DOMAIN = b"aeos-independent-assurance-proof-v1\x00"
_ATTESTATION_DOMAIN = b"aeos-independent-verifier-attestation-v1\x00"


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Mapping[str, Any], domain: bytes = _VERIFIER_DOMAIN) -> str:
    return hashlib.sha256(domain + _canonical(value).encode("utf-8")).hexdigest()


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not value:
        raise ValueError(f"proof_{field}_invalid")
    return value


def _verify_attestation(attestation: Mapping[str, Any], *, source_sha: str, iteration_id: str, evidence_ids: tuple[str, ...]) -> None:
    """Verify an attestation produced by the independent verifier boundary."""
    if attestation.get("schema_version") != "1.0":
        raise ValueError("verifier_attestation_schema_invalid")
    if attestation.get("issuer") != "AEOS_INDEPENDENT_VERIFIER":
        raise ValueError("verifier_attestation_issuer_invalid")
    if attestation.get("source_sha") != source_sha:
        raise ValueError("verifier_attestation_source_sha_mismatch")
    if attestation.get("iteration_id") != iteration_id:
        raise ValueError("verifier_attestation_iteration_mismatch")
    supplied_ids = attestation.get("evidence_ids")
    if not isinstance(supplied_ids, list) or tuple(supplied_ids) != evidence_ids:
        raise ValueError("verifier_attestation_evidence_mismatch")
    if attestation.get("verification_result") != "PASS":
        raise ValueError("verifier_attestation_not_pass")
    supplied_digest = attestation.get("attestation_digest")
    if not isinstance(supplied_digest, str) or not DIGEST_RE.fullmatch(supplied_digest):
        raise ValueError("verifier_attestation_digest_invalid")
    unsigned = {key: attestation[key] for key in attestation if key != "attestation_digest"}
    if supplied_digest != _digest(unsigned, _ATTESTATION_DOMAIN):
        raise ValueError("verifier_attestation_digest_mismatch")


def issue_assurance_proof(*, source_sha: str, iteration_id: str, evidence_ids: tuple[str, ...],
                          provenance_verified: bool, evidence_integrity_verified: bool,
                          forensic_result: str, independent_review: str, recommended_decision: str,
                          verifier_attestation: Mapping[str, Any], authority_packet: Mapping[str, Any],
                          pre_authority_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Freeze proof only after a separately produced verifier attestation."""
    if not SHA_RE.fullmatch(source_sha): raise ValueError("proof_source_sha_invalid")
    if not iteration_id: raise ValueError("proof_iteration_missing")
    if not evidence_ids or any(not DIGEST_RE.fullmatch(item) for item in evidence_ids):
        raise ValueError("proof_evidence_ids_invalid")
    if type(provenance_verified) is not bool or not provenance_verified:
        raise ValueError("proof_provenance_not_verified")
    if type(evidence_integrity_verified) is not bool or not evidence_integrity_verified:
        raise ValueError("proof_evidence_integrity_not_verified")
    if forensic_result != "PASS": raise ValueError("proof_forensic_not_pass")
    if independent_review != "PASS": raise ValueError("proof_independent_review_not_pass")
    if recommended_decision != "APPROVE": raise ValueError("proof_recommendation_not_approve")
    attestation = _require_mapping(verifier_attestation, "verifier_attestation")
    owner = _require_mapping(authority_packet, "authority_packet")
    pre = _require_mapping(pre_authority_packet, "pre_authority_packet")
    _verify_attestation(attestation, source_sha=source_sha, iteration_id=iteration_id, evidence_ids=evidence_ids)
    payload = {
        "schema_version": "1.0", "issuer": "AEOS_INDEPENDENT_VERIFIER",
        "source_sha": source_sha, "iteration_id": iteration_id, "evidence_ids": list(evidence_ids),
        "provenance_verified": True, "evidence_integrity_verified": True,
        "forensic_result": forensic_result, "independent_review": independent_review,
        "recommended_decision": recommended_decision, "verifier_attestation": dict(attestation),
        "authority_packet": dict(owner), "pre_authority_packet": dict(pre),
    }
    proof = dict(payload)
    proof["verification_seal"] = _digest(payload)
    proof["proof_digest"] = _digest(proof)
    return proof


def verify_assurance_proof(proof: Mapping[str, Any], *, source_sha: str, iteration_id: str, evidence_ids: tuple[str, ...]) -> None:
    """Verify proof identity, independent attestation, and deterministic integrity."""
    if proof.get("schema_version") != "1.0" or proof.get("issuer") != "AEOS_INDEPENDENT_VERIFIER":
        raise ValueError("proof_issuer_invalid")
    if proof.get("source_sha") != source_sha: raise ValueError("proof_source_sha_mismatch")
    if proof.get("iteration_id") != iteration_id: raise ValueError("proof_iteration_mismatch")
    supplied_ids = proof.get("evidence_ids")
    if not isinstance(supplied_ids, list) or tuple(supplied_ids) != evidence_ids:
        raise ValueError("proof_evidence_mismatch")
    if type(proof.get("provenance_verified")) is not bool or not proof["provenance_verified"]:
        raise ValueError("proof_provenance_not_verified")
    if type(proof.get("evidence_integrity_verified")) is not bool or not proof["evidence_integrity_verified"]:
        raise ValueError("proof_evidence_integrity_not_verified")
    if proof.get("forensic_result") != "PASS" or proof.get("independent_review") != "PASS":
        raise ValueError("proof_review_not_pass")
    if proof.get("recommended_decision") != "APPROVE":
        raise ValueError("proof_recommendation_not_approve")
    attestation = _require_mapping(proof.get("verifier_attestation"), "verifier_attestation")
    _verify_attestation(attestation, source_sha=source_sha, iteration_id=iteration_id, evidence_ids=evidence_ids)
    _require_mapping(proof.get("authority_packet"), "authority_packet")
    _require_mapping(proof.get("pre_authority_packet"), "pre_authority_packet")
    unsigned = {key: proof[key] for key in proof if key not in {"verification_seal", "proof_digest"}}
    if proof.get("verification_seal") != _digest(unsigned):
        raise ValueError("proof_verification_seal_invalid")
    expected_digest = _digest({key: proof[key] for key in proof if key != "proof_digest"})
    if proof.get("proof_digest") != expected_digest:
        raise ValueError("proof_digest_invalid")
