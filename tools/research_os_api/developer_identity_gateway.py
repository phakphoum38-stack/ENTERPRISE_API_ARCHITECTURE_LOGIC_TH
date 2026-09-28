"""Mint short-lived Developer Platform identity assertions from verified Research OS sessions.

The Research OS API is the trusted identity gateway. It verifies the canonical
Research OS session first, then signs a short-lived assertion for the separate
Developer Platform. The HMAC secret never leaves the server.
"""
from __future__ import annotations

import secrets
import time
from typing import Any

from developer_identity import IdentityAssertionError, IdentityAssertionVerifier


DEFAULT_MAX_AGE_SECONDS = 120


def _secret() -> str:
    import os

    value = (os.environ.get("RESEARCH_OS_IDENTITY_PROXY_SECRET") or "").strip()
    if not value:
        raise IdentityAssertionError("trusted identity gateway secret is not configured")
    return value


def mint_developer_assertion(
    session: dict[str, Any],
    *,
    now: int | None = None,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    """Create Developer assertion headers from an already verified session.

    The principal is derived server-side from the verified Research OS user_id.
    The caller cannot provide or override the principal.
    """
    user_id = str(session.get("user_id") or "").strip()
    email = str(session.get("email") or "").strip().lower()
    if not user_id or not email:
        raise IdentityAssertionError("verified session identity is incomplete")

    issued_at = int(time.time() if now is None else now)
    nonce = secrets.token_urlsafe(24)
    verifier = IdentityAssertionVerifier(
        _secret(),
        max_age_seconds=max_age_seconds,
    )
    signature = verifier.signature_for(user_id, issued_at, nonce)
    return {
        "principal": user_id,
        "email": email,
        "role": str(session.get("role") or "user").strip().lower(),
        "session_id": str(session.get("session_id") or ""),
        "issued_at": issued_at,
        "expires_at": issued_at + max_age_seconds,
        "headers": {
            "X-ResearchOS-Principal": user_id,
            "X-ResearchOS-Identity-Timestamp": str(issued_at),
            "X-ResearchOS-Identity-Nonce": nonce,
            "X-ResearchOS-Identity-Signature": signature,
        },
        "token_type": "research_os_developer_assertion",
        "assertion_mode": "signed_hmac_sha256",
    }
