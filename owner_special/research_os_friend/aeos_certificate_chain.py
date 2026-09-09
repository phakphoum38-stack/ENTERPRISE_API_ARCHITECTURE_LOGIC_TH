"""AEOS certificate-chain integrity boundary.

Certificates remain claims until their upstream evidence and verification are
independently validated. This module only guarantees chain linkage and
immutability of the certificate envelope.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping


class CertificateChainError(ValueError):
    """Raised when certificate-chain linkage is invalid."""


_SHA256 = 64


def _sha(value: str, name: str) -> None:
    if not isinstance(value, str) or len(value) != _SHA256 or any(c not in "0123456789abcdef" for c in value):
        raise CertificateChainError(f"invalid {name}")


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ChainCertificate:
    certificate_id: str
    certificate_type: str
    subject: str
    baseline_sha: str
    evidence_root: str
    provenance_root: str
    payload_digest: str
    previous_certificate_digest: str | None
    independently_verified: bool

    def __post_init__(self) -> None:
        if not isinstance(self.certificate_id, str) or not self.certificate_id:
            raise CertificateChainError("certificate_id required")
        if not isinstance(self.certificate_type, str) or not self.certificate_type:
            raise CertificateChainError("certificate_type required")
        if not isinstance(self.subject, str) or not self.subject:
            raise CertificateChainError("subject required")
        if not isinstance(self.baseline_sha, str) or len(self.baseline_sha) != 40 or any(c not in "0123456789abcdef" for c in self.baseline_sha):
            raise CertificateChainError("invalid baseline SHA")
        _sha(self.evidence_root, "evidence_root")
        _sha(self.provenance_root, "provenance_root")
        _sha(self.payload_digest, "payload_digest")
        if self.previous_certificate_digest is not None:
            _sha(self.previous_certificate_digest, "previous_certificate_digest")
        if type(self.independently_verified) is not bool:
            raise CertificateChainError("independently_verified must be bool")
        if not self.independently_verified:
            raise CertificateChainError("certificate chain requires independent verification")


def issue_chain_certificate(
    *,
    certificate_id: str,
    certificate_type: str,
    subject: str,
    baseline_sha: str,
    evidence_root: str,
    provenance_root: str,
    payload: Mapping[str, Any],
    previous_certificate: ChainCertificate | None = None,
    independently_verified: bool,
) -> ChainCertificate:
    """Create one immutable link after upstream verification has occurred."""
    if not isinstance(payload, Mapping) or not payload:
        raise CertificateChainError("certificate payload required")
    if type(independently_verified) is not bool or not independently_verified:
        raise CertificateChainError("certificate requires independent verification")
    if previous_certificate is not None:
        if previous_certificate.baseline_sha != baseline_sha:
            raise CertificateChainError("certificate baseline mismatch")
        if previous_certificate.evidence_root != evidence_root:
            raise CertificateChainError("certificate evidence root mismatch")
        if previous_certificate.provenance_root != provenance_root:
            raise CertificateChainError("certificate provenance root mismatch")
    _sha(evidence_root, "evidence_root")
    _sha(provenance_root, "provenance_root")
    payload_digest = _digest(payload)
    previous_digest = previous_certificate.payload_digest if previous_certificate else None
    return ChainCertificate(
        certificate_id=certificate_id,
        certificate_type=certificate_type,
        subject=subject,
        baseline_sha=baseline_sha,
        evidence_root=evidence_root,
        provenance_root=provenance_root,
        payload_digest=payload_digest,
        previous_certificate_digest=previous_digest,
        independently_verified=True,
    )


def verify_chain(*certificates: ChainCertificate) -> bool:
    """Verify ordering and immutable linkage without asserting subject truth."""
    if not certificates:
        raise CertificateChainError("certificate chain required")
    for index, certificate in enumerate(certificates):
        if not certificate.independently_verified:
            return False
        if index == 0:
            if certificate.previous_certificate_digest is not None:
                return False
            continue
        previous = certificates[index - 1]
        if certificate.previous_certificate_digest != previous.payload_digest:
            return False
        if certificate.baseline_sha != previous.baseline_sha:
            return False
        if certificate.evidence_root != previous.evidence_root:
            return False
        if certificate.provenance_root != previous.provenance_root:
            return False
    return True
