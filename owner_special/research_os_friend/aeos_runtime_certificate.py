"""Authoritative AEOS runtime-certificate boundary.

A runtime result is not a certificate merely because its JSON shape is valid.
This module binds the result to the exact baseline, contract, policy, evidence,
and provenance supplied by an independent verifier. The verification proof is
an externally produced artifact; a caller-supplied boolean is never accepted
as evidence of independent verification.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


class RuntimeCertificateError(ValueError):
    """Raised when a runtime certificate binding is invalid."""


_SHA256_HEX = 64
_GIT_SHA = 40


def _sha(value: str, *, length: int) -> None:
    if not isinstance(value, str) or len(value) != length or any(c not in "0123456789abcdef" for c in value):
        raise RuntimeCertificateError("invalid SHA binding")


def _digest(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class RuntimeCertificate:
    certificate_id: str
    baseline_sha: str
    contract_sha256: str
    policy_sha256: str
    evidence_root: str
    provenance_root: str
    test_manifest_sha256: str
    result_digest: str
    evidence_refs: tuple[str, ...]
    verification_proof: str

    def __post_init__(self) -> None:
        if not isinstance(self.certificate_id, str) or not self.certificate_id:
            raise RuntimeCertificateError("certificate_id required")
        _sha(self.baseline_sha, length=_GIT_SHA)
        for value in (self.contract_sha256, self.policy_sha256, self.evidence_root,
                      self.provenance_root, self.test_manifest_sha256, self.result_digest,
                      self.verification_proof):
            _sha(value, length=_SHA256_HEX)
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise RuntimeCertificateError("evidence_refs required")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise RuntimeCertificateError("duplicate evidence reference")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise RuntimeCertificateError("invalid evidence reference")


def certify_runtime_result(
    *,
    certificate_id: str,
    baseline_sha: str,
    observed_sha: str,
    contract_sha256: str,
    policy_sha256: str,
    evidence_root: str,
    provenance_root: str,
    test_manifest_sha256: str,
    result: Mapping[str, Any],
    evidence_refs: tuple[str, ...],
    verification_proof: str,
) -> RuntimeCertificate:
    """Bind a runtime result to immutable identity/proof inputs.

    ``verification_proof`` must be issued by the independent verification
    boundary. This function deliberately does not accept a boolean such as
    ``independently_verified=True`` because that would let the subject attest
    to its own trust status.
    """
    _sha(baseline_sha, length=_GIT_SHA)
    _sha(observed_sha, length=_GIT_SHA)
    if observed_sha != baseline_sha:
        raise RuntimeCertificateError("runtime result is stale")
    _sha(verification_proof, length=_SHA256_HEX)
    for value in (contract_sha256, policy_sha256, evidence_root, provenance_root, test_manifest_sha256):
        _sha(value, length=_SHA256_HEX)
    if not isinstance(result, Mapping) or not result:
        raise RuntimeCertificateError("runtime result required")
    if type(evidence_refs) is not tuple or not evidence_refs:
        raise RuntimeCertificateError("evidence_refs required")
    if len(set(evidence_refs)) != len(evidence_refs) or any(not isinstance(ref, str) or not ref.strip() for ref in evidence_refs):
        raise RuntimeCertificateError("invalid evidence references")
    result_digest = _digest(result)
    return RuntimeCertificate(
        certificate_id=certificate_id,
        baseline_sha=baseline_sha,
        contract_sha256=contract_sha256,
        policy_sha256=policy_sha256,
        evidence_root=evidence_root,
        provenance_root=provenance_root,
        test_manifest_sha256=test_manifest_sha256,
        result_digest=result_digest,
        evidence_refs=evidence_refs,
        verification_proof=verification_proof,
    )
