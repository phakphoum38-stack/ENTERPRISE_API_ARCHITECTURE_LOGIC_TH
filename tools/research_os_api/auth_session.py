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
import re
import secrets
import tempfile
import time
from pathlib import Path
from typing import Any

SESSION_COOKIE = "research_os_session"
DEFAULT_TTL_SECONDS = 8 * 60 * 60
_SAFE_USER_ID = re.compile(r"^[A-Za-z0-9._-]+$")


def _secret() -> bytes:
    value = (os.getenv("RESEARCH_OS_SESSION_SECRET") or "").strip()
    if not value:
        raise RuntimeError("RESEARCH_OS_SESSION_SECRET is required")
    return value.encode("utf-8")


def _data_root() -> Path:
    configured = (os.getenv("RESEARCH_OS_V3_DATA_DIR") or "").strip()
    if configured:
        return Path(configured).expanduser()
    if os.name == "nt":
        return Path(os.getenv("PROGRAMDATA") or r"C:\ProgramData") / "ResearchOSV3"
    xdg = (os.getenv("XDG_DATA_HOME") or "").strip()
    if xdg:
        return Path(xdg).expanduser() / "research-os-v3"
    return Path.home() / ".local" / "share" / "research-os-v3"


def _user_scope(user_id: str) -> Path:
    value = str(user_id or "").strip()
    if not value or not _SAFE_USER_ID.fullmatch(value) or value in {".", ".."}:
        raise ValueError("invalid user id for session state")
    return _data_root() / "users" / value / "profiles" / "default" / "sessions"


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
        if not payload.get("session_id"):
            raise ValueError("session id is missing")
        return payload
    except (ValueError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("invalid research session") from exc


class SessionRevocationStore:
    """Durable per-user revocation markers in the canonical V3 data root."""

    def _scope(self, user_id: str) -> Path:
        scope = _user_scope(user_id)
        scope.mkdir(parents=True, exist_ok=True)
        return scope / "revocation"

    def _marker(self, user_id: str, session_id_value: str) -> Path:
        if not session_id_value or "/" in session_id_value or "\\" in session_id_value:
            raise ValueError("invalid session id")
        directory = self._scope(user_id)
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{session_id_value}.revoked"

    def revoke(self, user_id: str, session_id_value: str) -> None:
        marker = self._marker(user_id, session_id_value)
        marker.write_text(str(int(time.time())), encoding="utf-8")

    def revoke_all(self, user_id: str) -> None:
        marker = self._scope(user_id) / "all.revoked"
        marker.write_text(str(int(time.time())), encoding="utf-8")

    def is_revoked(self, session_id_value: str, user_id: str, issued_at: int | None = None) -> bool:
        marker = self._marker(user_id, session_id_value)
        if marker.exists():
            return True
        all_marker = marker.parent / "all.revoked"
        if not all_marker.exists() or issued_at is None:
            return False
        try:
            return int(issued_at) <= int(all_marker.read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            return False


def session_id(token: str) -> str:
    return str(_decode(token)["session_id"])


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


def revoke_session(token: str) -> None:
    payload = _decode(token)
    SessionRevocationStore().revoke(str(payload["user_id"]), str(payload["session_id"]))


def revoke_all_sessions(user_id: str) -> None:
    SessionRevocationStore().revoke_all(user_id)


def verify_session(token: str | None) -> dict[str, Any]:
    if not token:
        raise ValueError("authentication required")
    payload = _decode(token)
    if SessionRevocationStore().is_revoked(
        str(payload["session_id"]),
        str(payload["user_id"]),
        int(payload["iat"]),
    ):
        raise ValueError("session revoked")
    return payload


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
