"""Per-user Research OS session primitives.

This module deliberately contains no Google OAuth exchange logic.  Google
Identity establishes the principal; this module binds that principal to a
short-lived, signed Research OS session that API handlers can verify.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

SESSION_COOKIE = "research_os_session"
DEFAULT_TTL_SECONDS = 8 * 60 * 60


def _secret() -> bytes:
    value = (os.getenv("RESEARCH_OS_SESSION_SECRET") or "").strip()
    if not value:
        raise RuntimeError("RESEARCH_OS_SESSION_SECRET is required")
    return value.encode("utf-8")


def _encode(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
    signature = hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest()
    sig = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")
    return f"{body}.{sig}"


def _decode(token: str) -> dict[str, Any]:
    try:
        body, supplied = token.split(".", 1)
        expected = hmac.new(_secret(), body.encode("ascii"), hashlib.sha256).digest()
        expected_text = base64.urlsafe_b64encode(expected).rstrip(b"=").decode("ascii")
        if not hmac.compare_digest(supplied, expected_text):
            raise ValueError("invalid session signature")
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("invalid session payload")
        if int(payload.get("exp", 0)) <= int(time.time()):
            raise ValueError("session expired")
        if not payload.get("user_id") or not payload.get("email"):
            raise ValueError("session identity is incomplete")
        return payload
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("invalid research session") from exc


def issue_session(account: dict[str, Any], *, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    email = str(account.get("email") or "").strip().lower()
    if not email:
        raise ValueError("Google identity email is required")
    user_id = str(account.get("sub") or account.get("id") or email).strip()
    role = str(account.get("role") or "user").strip().lower()
    now = int(time.time())
    payload = {
        "session_id": secrets.token_urlsafe(18),
        "user_id": user_id,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + max(60, int(ttl_seconds)),
    }
    return _encode(payload)


def verify_session(token: str | None) -> dict[str, Any]:
    if not token:
        raise ValueError("authentication required")
    return _decode(token)


def cookie_header(token: str, *, secure: bool = True) -> str:
    flags = [
        f"{SESSION_COOKIE}={token}",
        "Path=/",
        "HttpOnly",
        "SameSite=Lax",
    ]
    if secure:
        flags.append("Secure")
    return "; ".join(flags)


def clear_cookie_header() -> str:
    return f"{SESSION_COOKIE}=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0"
