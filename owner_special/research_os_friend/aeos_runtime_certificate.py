"""Authoritative AEOS runtime-certificate boundary.

A runtime result is not a certificate merely because its JSON shape is valid.
This module binds the result to the exact baseline, contract, policy, evidence,
and provenance supplied by an independent verifier.
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
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
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
    independently_verified: bool = True

    def __post_init__(self) -> None:
        if not self.certificate_id or not isinstance(self.certificate_id, str):
            raise RuntimeCertificateError("certificate_id required")
        _sha(self.baseline_sha, length=_GIT_SHA)
        for value in (self.contract_sha256, self.policy_sha256, self.evidence_root,
                      self.provenance_root, self.test_manifest_sha256, self.result_digest):
            _sha(value, length=_SHA256_HEX)
        if not isinstance(self.evidence_refs, tuple) or not self.evidence_refs:
            raise RuntimeCertificateError("evidence_refs required")
        if any(not isinstance(ref, str) or not ref for ref in self.evidence_refs):
            raise RuntimeCertificateError("invalid evidence reference")
        if type(self.independently_verified) is not bool or not self.independently_verified:
            raise RuntimeCertificateError("certificate requires independent verification")


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
    independently_verified: bool,
) -> RuntimeCertificate:
    """Bind a runtime result to immutable identity/proof inputs.

    The function performs no repository, CI, or authority lookup. Callers must
    obtain those observations from an independent verification boundary first.
    """
    _sha(baseline_sha, length=_GIT_SHA)
    _sha(observed_sha, length=_GIT_SHA)
    if observed_sha != baseline_sha:
        raise RuntimeCertificateError("runtime result is stale")
    if type(independently_verified) is not bool or not independently_verified:
        raise RuntimeCertificateError("runtime result is not independently verified")
    for value in (contract_sha256, policy_sha256, evidence_root, provenance_root, test_manifest_sha256):
        _sha(value, length=_SHA256_HEX)
    if not isinstance(result, Mapping) or not result:
        raise RuntimeCertificateError("runtime result required")
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
        evidence_refs=tuple(evidence_refs),
        independently_verified=True,
    )
