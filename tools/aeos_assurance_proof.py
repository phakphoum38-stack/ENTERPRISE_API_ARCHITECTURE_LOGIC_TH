#!/usr/bin/env python3
"""Verifier-issued, target-bound assurance proof for the AEOS master boundary.

This module is deliberately separate from execution. A proof is minted only
from a verified assurance payload and carries a verifier-derived seal. The
master composition boundary verifies the seal and exact identity before it can
produce READY_FOR_OWNER_AUTHORITY.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_VERIFIER_DOMAIN = b"aeos-independent-assurance-proof-v1\x00"
_VERIFIER_SEAL = "AEOS-INDEPENDENT-VERIFIER-SEAL-v1"


def _canonical(value: Mapping[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_VERIFIER_DOMAIN + _canonical(value).encode("utf-8")).hexdigest()


def issue_assurance_proof(
    *,
    source_sha: str,
    iteration_id: str,
    evidence_ids: tuple[str, ...],
    provenance_verified: bool,
    evidence_integrity_verified: bool,
    forensic_result: str,
    independent_review: str,
    recommended_decision: str,
) -> dict[str, Any]:
    """Mint proof only from strict, already-verified observations."""
    if not SHA_RE.fullmatch(source_sha):
        raise ValueError("proof_source_sha_invalid")
    if not iteration_id:
        raise ValueError("proof_iteration_missing")
    if not evidence_ids or any(not DIGEST_RE.fullmatch(item) for item in evidence_ids):
        raise ValueError("proof_evidence_ids_invalid")
    if type(provenance_verified) is not bool or not provenance_verified:
        raise ValueError("proof_provenance_not_verified")
    if type(evidence_integrity_verified) is not bool or not evidence_integrity_verified:
        raise ValueError("proof_evidence_integrity_not_verified")
    if forensic_result != "PASS":
        raise ValueError("proof_forensic_not_pass")
    if independent_review != "PASS":
        raise ValueError("proof_independent_review_not_pass")
    if recommended_decision != "APPROVE":
        raise ValueError("proof_recommendation_not_approve")

    payload = {
        "schema_version": "1.0",
        "issuer": "AEOS_INDEPENDENT_VERIFIER",
        "source_sha": source_sha,
        "iteration_id": iteration_id,
        "evidence_ids": list(evidence_ids),
        "provenance_verified": True,
        "evidence_integrity_verified": True,
        "forensic_result": forensic_result,
        "independent_review": independent_review,
        "recommended_decision": recommended_decision,
    }
    proof = dict(payload)
    proof["verification_seal"] = hashlib.sha256(
        _VERIFIER_DOMAIN + _VERIFIER_SEAL.encode("utf-8") + _canonical(payload).encode("utf-8")
    ).hexdigest()
    proof["proof_digest"] = _digest(proof)
    return proof


def verify_assurance_proof(proof: Mapping[str, Any], *, source_sha: str, iteration_id: str, evidence_ids: tuple[str, ...]) -> None:
    """Verify verifier-issued proof against the exact execution identity."""
    if proof.get("schema_version") != "1.0" or proof.get("issuer") != "AEOS_INDEPENDENT_VERIFIER":
        raise ValueError("proof_issuer_invalid")
    if proof.get("source_sha") != source_sha:
        raise ValueError("proof_source_sha_mismatch")
    if proof.get("iteration_id") != iteration_id:
        raise ValueError("proof_iteration_mismatch")
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
    unsigned = {key: proof[key] for key in proof if key not in {"verification_seal", "proof_digest"}}
    expected_seal = hashlib.sha256(
        _VERIFIER_DOMAIN + _VERIFIER_SEAL.encode("utf-8") + _canonical(unsigned).encode("utf-8")
    ).hexdigest()
    if proof.get("verification_seal") != expected_seal:
        raise ValueError("proof_verification_seal_invalid")
    expected_digest = _digest({key: proof[key] for key in proof if key != "proof_digest"})
    if proof.get("proof_digest") != expected_digest:
        raise ValueError("proof_digest_invalid")
