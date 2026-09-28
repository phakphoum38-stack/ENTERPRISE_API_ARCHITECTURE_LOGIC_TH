"""Reusable API authentication guard for Research OS HTTP handlers.

The handler layer owns the HTTP response.  This module only resolves the
trusted per-user session from the request headers/cookies and deliberately
never accepts user/role identity from arbitrary request fields.
"""
from __future__ import annotations

from http.cookies import SimpleCookie
from typing import Any, Mapping

try:
    from .auth_session import SESSION_COOKIE, verify_session
except ImportError:
    from auth_session import SESSION_COOKIE, verify_session

SESSION_HEADER = "X-Research-OS-Session"
OAUTH_HANDOFF_HEADER = "X-Research-OS-OAuth-State"


def extract_session_token(headers: Mapping[str, str]) -> str | None:
    """Return a verified-session candidate from header, one-time OAuth handoff, or cookie."""
    header_token = ""
    for name, value in headers.items():
        if str(name).casefold() == SESSION_HEADER.casefold():
            header_token = str(value or "").strip()
            break
    if header_token:
        return header_token

    # Native clients cannot share the browser's HttpOnly cookie jar. During
    # Google sign-in they send the OAuth state once; the backend consumes the
    # matching handoff and returns the real signed session token.
    handoff_code = ""
    for name, value in headers.items():
        if str(name).casefold() == OAUTH_HANDOFF_HEADER.casefold():
            handoff_code = str(value or "").strip()
            break
    if handoff_code:
        try:
            try:
                from .google_identity import GoogleIdentityBroker
                from .oauth_handoff import consume_handoff
            except ImportError:
                from google_identity import GoogleIdentityBroker
                from oauth_handoff import consume_handoff
            session = consume_handoff(GoogleIdentityBroker().root, handoff_code)
            if session:
                return session
        except Exception:
            return None

    raw_cookie = headers.get("Cookie") or ""
    if not raw_cookie:
        for name, value in headers.items():
            if str(name).casefold() == "cookie":
                raw_cookie = str(value or "")
                break
    if not raw_cookie:
        return None
    cookie = SimpleCookie()
    try:
        cookie.load(raw_cookie)
    except Exception:
        return None
    morsel = cookie.get(SESSION_COOKIE)
    return morsel.value if morsel else None


def require_session(headers: Mapping[str, str]) -> dict[str, Any]:
    """Resolve a verified Research OS principal or fail closed."""
    return verify_session(extract_session_token(headers))
