#!/usr/bin/env python3
"""Email OTP identity and cloud profile storage for Research OS.

The service is dependency-free. SMTP and token secrets are supplied only through
server environment variables. No email addresses, OTPs, or session tokens are
stored in the repository.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Any

OTP_TTL_SECONDS = 10 * 60
SESSION_TTL_SECONDS = 30 * 24 * 60 * 60
MAX_ATTEMPTS = 6


def _data_dir() -> Path:
    configured = os.getenv("RESEARCH_OS_DATA_DIR", "").strip()
    base = Path(configured).expanduser() if configured else Path.home() / ".research_os"
    path = base / "identity"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state_path() -> Path:
    return _data_dir() / "email_identity.json"


def _load_state() -> dict[str, Any]:
    path = _state_path()
    if not path.exists():
        return {"challenges": {}, "profiles": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"challenges": {}, "profiles": {}}
    return value if isinstance(value, dict) else {"challenges": {}, "profiles": {}}


def _save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def normalize_email(value: str) -> str:
    email = value.strip().lower()
    if not email or "@" not in email:
        raise ValueError("valid email is required")
    local, _, domain = email.partition("@")
    if not local or "." not in domain or domain.startswith(".") or domain.endswith("."):
        raise ValueError("valid email is required")
    return email


def _email_id(email: str) -> str:
    return hashlib.sha256(normalize_email(email).encode("utf-8")).hexdigest()


def _secret() -> bytes:
    value = os.getenv("RESEARCH_OS_IDENTITY_SECRET", "").strip()
    if len(value) < 32:
        raise RuntimeError("RESEARCH_OS_IDENTITY_SECRET must be configured with at least 32 characters")
    return value.encode("utf-8")


def configured() -> bool:
    required = (
        "RESEARCH_OS_IDENTITY_SECRET",
        "RESEARCH_OS_SMTP_HOST",
        "RESEARCH_OS_SMTP_FROM",
    )
    return all(os.getenv(key, "").strip() for key in required)


def _hash_code(challenge_id: str, code: str) -> str:
    return hmac.new(_secret(), f"{challenge_id}:{code}".encode("utf-8"), hashlib.sha256).hexdigest()


def _send_code(email: str, code: str) -> None:
    host = os.getenv("RESEARCH_OS_SMTP_HOST", "").strip()
    sender = os.getenv("RESEARCH_OS_SMTP_FROM", "").strip()
    if not host or not sender:
        raise RuntimeError("Email verification is not configured")
    port = int(os.getenv("RESEARCH_OS_SMTP_PORT", "587"))
    username = os.getenv("RESEARCH_OS_SMTP_USERNAME", "").strip()
    password = os.getenv("RESEARCH_OS_SMTP_PASSWORD", "")
    use_ssl = os.getenv("RESEARCH_OS_SMTP_SSL", "0").strip() == "1"

    message = EmailMessage()
    message["Subject"] = "Research OS verification code"
    message["From"] = sender
    message["To"] = email
    message.set_content(
        "Your Research OS verification code is: " + code + "\n\n"
        "The code expires in 10 minutes. If you did not request this code, ignore this email."
    )

    if use_ssl:
        client: smtplib.SMTP = smtplib.SMTP_SSL(host, port, context=ssl.create_default_context(), timeout=15)
    else:
        client = smtplib.SMTP(host, port, timeout=15)
        client.starttls(context=ssl.create_default_context())
    try:
        if username:
            client.login(username, password)
        client.send_message(message)
    finally:
        client.quit()


def request_code(email_value: str) -> dict[str, Any]:
    if not configured():
        raise RuntimeError("Email verification is not configured on this server")
    email = normalize_email(email_value)
    now = int(time.time())
    challenge_id = secrets.token_urlsafe(24)
    code = f"{secrets.randbelow(1_000_000):06d}"
    state = _load_state()
    challenges = state.setdefault("challenges", {})
    # Remove expired challenges while touching state.
    for key in list(challenges):
        if int(challenges[key].get("expires_at", 0)) < now:
            challenges.pop(key, None)
    challenges[challenge_id] = {
        "email_id": _email_id(email),
        "email": email,
        "code_hash": _hash_code(challenge_id, code),
        "expires_at": now + OTP_TTL_SECONDS,
        "attempts": 0,
    }
    _save_state(state)
    _send_code(email, code)
    return {"challenge_id": challenge_id, "expires_in": OTP_TTL_SECONDS}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64url(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _issue_token(email: str) -> tuple[str, int]:
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    payload = {
        "sub": _email_id(email),
        "email": normalize_email(email),
        "exp": expires_at,
        "nonce": secrets.token_urlsafe(12),
    }
    encoded = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _b64url(hmac.new(_secret(), encoded.encode("ascii"), hashlib.sha256).digest())
    return f"{encoded}.{signature}", expires_at


def verify_code(challenge_id: str, code: str) -> dict[str, Any]:
    state = _load_state()
    challenges = state.setdefault("challenges", {})
    challenge = challenges.get(challenge_id)
    if not isinstance(challenge, dict):
        raise ValueError("verification challenge not found or expired")
    now = int(time.time())
    if int(challenge.get("expires_at", 0)) < now:
        challenges.pop(challenge_id, None)
        _save_state(state)
        raise ValueError("verification code expired")
    attempts = int(challenge.get("attempts", 0)) + 1
    challenge["attempts"] = attempts
    if attempts > MAX_ATTEMPTS:
        challenges.pop(challenge_id, None)
        _save_state(state)
        raise ValueError("too many verification attempts")
    candidate = _hash_code(challenge_id, str(code).strip())
    if not hmac.compare_digest(candidate, str(challenge.get("code_hash", ""))):
        _save_state(state)
        raise ValueError("verification code is invalid")

    email = normalize_email(str(challenge["email"]))
    challenges.pop(challenge_id, None)
    profiles = state.setdefault("profiles", {})
    key = _email_id(email)
    profile = profiles.get(key)
    if not isinstance(profile, dict):
        profile = {"email": email, "preferences": {}, "updated_at": now}
        profiles[key] = profile
    _save_state(state)
    token, expires_at = _issue_token(email)
    return {
        "token": token,
        "expires_at": expires_at,
        "profile": {"email": email, "preferences": profile.get("preferences", {})},
    }


def authorize(header_value: str | None) -> dict[str, Any]:
    value = (header_value or "").strip()
    if value.lower().startswith("bearer "):
        value = value[7:].strip()
    if "." not in value:
        raise PermissionError("owner session is missing")
    encoded, signature = value.rsplit(".", 1)
    expected = _b64url(hmac.new(_secret(), encoded.encode("ascii"), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected):
        raise PermissionError("owner session is invalid")
    try:
        payload = json.loads(_unb64url(encoded).decode("utf-8"))
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PermissionError("owner session is invalid") from exc
    if int(payload.get("exp", 0)) < int(time.time()):
        raise PermissionError("owner session expired")
    return payload


def get_profile(authorization: str | None) -> dict[str, Any]:
    identity = authorize(authorization)
    state = _load_state()
    profile = state.setdefault("profiles", {}).get(identity["sub"], {})
    return {
        "email": identity["email"],
        "preferences": profile.get("preferences", {}) if isinstance(profile, dict) else {},
        "private_sync": False,
    }


def update_preferences(authorization: str | None, preferences: Any) -> dict[str, Any]:
    identity = authorize(authorization)
    if not isinstance(preferences, dict):
        raise ValueError("preferences must be an object")
    # Identity sync intentionally accepts only non-secret product preferences.
    allowed = {"theme", "language", "api_auto_discovery", "api_scan_lan", "heartbeat_seconds"}
    clean = {str(key): value for key, value in preferences.items() if str(key) in allowed}
    state = _load_state()
    profiles = state.setdefault("profiles", {})
    profile = profiles.get(identity["sub"])
    if not isinstance(profile, dict):
        profile = {"email": identity["email"], "preferences": {}}
        profiles[identity["sub"]] = profile
    profile["preferences"] = clean
    profile["updated_at"] = int(time.time())
    _save_state(state)
    return {"email": identity["email"], "preferences": clean, "private_sync": False}
