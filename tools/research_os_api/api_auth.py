"""Reusable API authentication guard for Research OS HTTP handlers.

The handler layer owns the HTTP response.  This module only resolves the
trusted per-user session from the request headers/cookies and deliberately
never accepts user/role identity from arbitrary request fields.
"""
from __future__ import annotations

from http.cookies import SimpleCookie
from typing import Any, Mapping

try:  # Package import for normal application execution.
    from .auth_session import SESSION_COOKIE, verify_session
except ImportError:  # Top-level import used by the repository's unittest discovery.
    from auth_session import SESSION_COOKIE, verify_session

SESSION_HEADER = "X-Research-OS-Session"


def extract_session_token(headers: Mapping[str, str]) -> str | None:
    """Return a session token from the trusted session header or cookie.

    Header takes precedence for internal/test clients.  The cookie is the
    browser-facing mechanism.  No role, email, or user id is accepted from
    request JSON or query parameters.
    """
    header_token = (headers.get(SESSION_HEADER) or "").strip()
    if header_token:
        return header_token
    raw_cookie = headers.get("Cookie") or ""
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
