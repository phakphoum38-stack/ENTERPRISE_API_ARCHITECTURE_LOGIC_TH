"""Trusted identity assertions for the Research OS Developer Platform.

The external identity gateway authenticates the human and forwards a short-lived,
HMAC-signed assertion to Developer Platform. The API never accepts a principal
header by itself in production mode.
"""
from __future__ import annotations

import hashlib
import hmac
import re
import threading
import time
from dataclasses import dataclass
from typing import Mapping

_NONCE_RE = re.compile(r"^[A-Za-z0-9._~-]{16,128}$")


class IdentityAssertionError(PermissionError):
    """Raised when a gateway identity assertion cannot be trusted."""


@dataclass(frozen=True)
class VerifiedIdentity:
    principal: str
    issued_at: int
    nonce: str
    mode: str = "signed_assertion"


class IdentityAssertionVerifier:
    """Verify bounded-lifetime HMAC assertions and reject nonce replay."""

    def __init__(self, secret: str, *, max_age_seconds: int = 120, future_skew_seconds: int = 30):
        secret = secret.strip()
        if len(secret.encode("utf-8")) < 16:
            raise IdentityAssertionError("trusted identity gateway secret is missing or too short")
        if max_age_seconds < 10 or max_age_seconds > 900:
            raise IdentityAssertionError("identity assertion max age must be between 10 and 900 seconds")
        self._secret = secret.encode("utf-8")
        self._max_age = int(max_age_seconds)
        self._future_skew = max(0, min(int(future_skew_seconds), 120))
        self._lock = threading.RLock()
        self._seen_nonces: dict[str, int] = {}

    @staticmethod
    def canonical_message(principal: str, issued_at: int, nonce: str) -> bytes:
        return f"{principal}\n{issued_at}\n{nonce}".encode("utf-8")

    def signature_for(self, principal: str, issued_at: int, nonce: str) -> str:
        return hmac.new(
            self._secret,
            self.canonical_message(principal, issued_at, nonce),
            hashlib.sha256,
        ).hexdigest()

    def verify(self, headers: Mapping[str, str], *, now: int | None = None) -> VerifiedIdentity:
        principal = (headers.get("X-ResearchOS-Principal") or "").strip()
        timestamp_text = (headers.get("X-ResearchOS-Identity-Timestamp") or "").strip()
        nonce = (headers.get("X-ResearchOS-Identity-Nonce") or "").strip()
        supplied_signature = (headers.get("X-ResearchOS-Identity-Signature") or "").strip().lower()
        if not principal or len(principal) > 256 or any(ch in principal for ch in "\r\n\x00"):
            raise IdentityAssertionError("authenticated principal is missing or invalid")
        try:
            issued_at = int(timestamp_text)
        except (TypeError, ValueError) as exc:
            raise IdentityAssertionError("identity assertion timestamp is missing or invalid") from exc
        if not _NONCE_RE.fullmatch(nonce):
            raise IdentityAssertionError("identity assertion nonce is missing or invalid")
        if len(supplied_signature) != 64:
            raise IdentityAssertionError("identity assertion signature is missing or invalid")

        current = int(time.time() if now is None else now)
        age = current - issued_at
        if age > self._max_age:
            raise IdentityAssertionError("identity assertion has expired")
        if age < -self._future_skew:
            raise IdentityAssertionError("identity assertion timestamp is too far in the future")

        expected = self.signature_for(principal, issued_at, nonce)
        if not hmac.compare_digest(expected, supplied_signature):
            raise IdentityAssertionError("trusted identity gateway signature verification failed")

        expiry = issued_at + self._max_age + self._future_skew
        with self._lock:
            self._seen_nonces = {key: value for key, value in self._seen_nonces.items() if value >= current}
            if nonce in self._seen_nonces:
                raise IdentityAssertionError("identity assertion replay detected")
            self._seen_nonces[nonce] = expiry
        return VerifiedIdentity(principal=principal, issued_at=issued_at, nonce=nonce)
