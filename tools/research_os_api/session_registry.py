"""Durable Research OS platform session registry.

The registry stores session metadata only; signed session tokens and OAuth
access tokens are never persisted here.
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

try:
    from .identity_storage import storage_key
except ImportError:  # pragma: no cover
    from identity_storage import storage_key

REGISTRY_FILENAME = "registry.json"


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


def _scope(user_id: str) -> Path:
    return _data_root() / "users" / storage_key(user_id) / "profiles" / "default" / "sessions"


def _path(user_id: str) -> Path:
    return _scope(user_id) / REGISTRY_FILENAME


def _load(user_id: str) -> list[dict[str, Any]]:
    path = _path(user_id)
    if not path.exists():
        return []
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _save(user_id: str, records: list[dict[str, Any]]) -> None:
    path = _path(user_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".registry-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(records, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def register_session(
    *,
    session_id: str,
    user_id: str,
    email: str,
    role: str,
    provider: str | None = None,
    issued_at: int | None = None,
    expires_at: int | None = None,
    source_sha: str | None = None,
) -> dict[str, Any]:
    now = int(time.time())
    record = {
        "session_id": str(session_id),
        "user_id": str(user_id),
        "email": str(email).strip().lower(),
        "role": str(role).strip().lower(),
        "provider": str(provider).strip().lower() if provider else None,
        "issued_at": int(issued_at if issued_at is not None else now),
        "expires_at": int(expires_at if expires_at is not None else now),
        "last_seen_at": now,
        "revoked": False,
    }
    if source_sha:
        record["source_sha"] = str(source_sha)
    records = [item for item in _load(user_id) if item.get("session_id") != session_id]
    records.append(record)
    _save(user_id, records)
    return dict(record)


def touch_session(user_id: str, session_id: str) -> None:
    records = _load(user_id)
    now = int(time.time())
    changed = False
    for item in records:
        if item.get("session_id") == session_id and not item.get("revoked"):
            item["last_seen_at"] = now
            changed = True
            break
    if changed:
        _save(user_id, records)


def mark_revoked(user_id: str, session_id: str) -> bool:
    records = _load(user_id)
    changed = False
    for item in records:
        if item.get("session_id") == session_id:
            item["revoked"] = True
            item["revoked_at"] = int(time.time())
            changed = True
            break
    if changed:
        _save(user_id, records)
    return changed


def mark_all_revoked(user_id: str) -> int:
    records = _load(user_id)
    now = int(time.time())
    changed = 0
    for item in records:
        if not item.get("revoked"):
            item["revoked"] = True
            item["revoked_at"] = now
            changed += 1
    if records:
        _save(user_id, records)
    return changed


def list_sessions(user_id: str, *, include_revoked: bool = False) -> list[dict[str, Any]]:
    now = int(time.time())
    result = []
    for item in _load(user_id):
        if not include_revoked and item.get("revoked"):
            continue
        if int(item.get("expires_at", 0)) <= now:
            continue
        result.append(dict(item))
    return sorted(result, key=lambda item: int(item.get("last_seen_at", 0)), reverse=True)


def get_session(user_id: str, session_id: str) -> dict[str, Any] | None:
    for item in _load(user_id):
        if item.get("session_id") == session_id:
            return dict(item)
    return None
