"""Short-lived, single-use OAuth/QR handoff without persisting session bearer tokens.

The handoff code is an opaque, high-entropy capability. Only a digest of the
code is persisted. The referenced canonical session is resolved through the
durable Session Registry and a fresh Research OS session is issued on consume.
This keeps QR/native handoff state outside the execution/authorization plane.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
import time
from pathlib import Path
from threading import Lock
from typing import Any

try:
    from .auth_session import issue_session, verify_session
    from .session_registry import get_session
except ImportError:  # pragma: no cover
    from auth_session import issue_session, verify_session
    from session_registry import get_session

TTL_SECONDS = 120
_LOCK = Lock()


def _digest(code: str) -> str:
    return hashlib.sha256(code.encode("utf-8")).hexdigest()


def _write(path: Path, data: dict[str, Any]) -> None:
    fd, temp_name = tempfile.mkstemp(prefix=".oauth-handoff-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, separators=(",", ":"), sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def create_handoff(
    root: Path,
    session: str,
    redirect_uri: str,
    *,
    code: str | None = None,
    audience: str = "native",
) -> str:
    """Create a short-lived one-time handoff bound to a live canonical session."""
    principal = verify_session(session)
    handoff_code = code or secrets.token_urlsafe(32)
    redirect = str(redirect_uri or "").strip()
    aud = str(audience or "").strip()
    if not redirect:
        raise ValueError("redirect_uri is required")
    if not aud:
        raise ValueError("audience is required")

    now = int(time.time())
    path = root / "oauth_handoffs.json"
    root.mkdir(parents=True, exist_ok=True)
    record = {
        "session_id": str(principal["session_id"]),
        "user_id": str(principal["user_id"]),
        "email": str(principal["email"]),
        "role": str(principal["role"]),
        "provider": str(principal.get("provider") or ""),
        "issued_at": int(principal["iat"]),
        "exp": now + TTL_SECONDS,
        "redirect_uri": redirect,
        "audience": aud,
    }
    with _LOCK:
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, ValueError, TypeError):
            data = {}
        data = {
            k: v
            for k, v in data.items()
            if isinstance(v, dict) and int(v.get("exp", 0)) > now
        }
        data[_digest(handoff_code)] = record
        _write(path, data)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    return handoff_code


def consume_handoff(
    root: Path,
    code: str,
    *,
    expected_redirect_uri: str | None = None,
    expected_audience: str | None = None,
) -> str | None:
    """Consume a handoff once and rotate it into a fresh canonical session.

    No session bearer token is persisted in the handoff store. Consumption
    fails closed if the referenced source session is missing, expired, or
    revoked in the canonical Session Registry.
    """
    value = str(code or "").strip()
    if not value:
        return None
    path = root / "oauth_handoffs.json"
    now = int(time.time())
    with _LOCK:
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, ValueError, TypeError):
            data = {}
        key = _digest(value)
        item = data.pop(key, None)
        data = {
            k: v
            for k, v in data.items()
            if isinstance(v, dict) and int(v.get("exp", 0)) > now
        }
        try:
            _write(path, data)
        except OSError:
            return None

    if not isinstance(item, dict) or int(item.get("exp", 0)) <= now:
        return None
    redirect = str(item.get("redirect_uri") or "")
    audience = str(item.get("audience") or "")
    if expected_redirect_uri is not None and redirect != str(expected_redirect_uri).strip():
        return None
    if expected_audience is not None and audience != str(expected_audience).strip():
        return None

    user_id = str(item.get("user_id") or "")
    source_session_id = str(item.get("session_id") or "")
    source = get_session(user_id, source_session_id)
    if not isinstance(source, dict):
        return None
    if bool(source.get("revoked")) or int(source.get("expires_at", 0)) <= now:
        return None
    if int(source.get("issued_at", 0)) != int(item.get("issued_at", -1)):
        return None
    if str(source.get("email") or "").lower() != str(item.get("email") or "").lower():
        return None

    principal = {
        "user_id": user_id,
        "email": str(source.get("email") or ""),
        "role": str(source.get("role") or "user"),
        "provider": str(source.get("provider") or "") or None,
    }
    return issue_session(principal)
