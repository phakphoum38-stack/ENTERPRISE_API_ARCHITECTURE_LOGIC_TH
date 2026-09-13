"""Short-lived one-time OAuth handoff state for native desktop clients."""
from __future__ import annotations

import json
import secrets
import time
from pathlib import Path
from threading import Lock
from typing import Any

TTL_SECONDS = 120
_LOCK = Lock()


def create_handoff(root: Path, session: str, redirect_uri: str, *, code: str | None = None) -> str:
    """Store a session behind a short-lived, single-use opaque code."""
    handoff_code = code or secrets.token_urlsafe(32)
    now = int(time.time())
    path = root / "oauth_handoffs.json"
    root.mkdir(parents=True, exist_ok=True)
    with _LOCK:
        try:
            data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        except (OSError, ValueError, TypeError):
            data = {}
        data = {k: v for k, v in data.items() if int(v.get("exp", 0)) > now}
        data[handoff_code] = {"session": session, "redirect_uri": redirect_uri, "exp": now + TTL_SECONDS}
        path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        try:
            path.chmod(0o600)
        except OSError:
            pass
    return handoff_code


def consume_handoff(root: Path, code: str) -> str | None:
    """Consume a handoff exactly once and return its session token."""
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
        item = data.pop(value, None)
        data = {k: v for k, v in data.items() if int(v.get("exp", 0)) > now}
        try:
            path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
        except OSError:
            pass
    if not isinstance(item, dict) or int(item.get("exp", 0)) <= now:
        return None
    session = str(item.get("session") or "").strip()
    return session or None
