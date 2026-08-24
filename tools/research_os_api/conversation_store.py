#!/usr/bin/env python3
"""Authenticated conversation store for Research OS local/cloud sync."""

from __future__ import annotations

import json
import os
import re
import secrets
import threading
from pathlib import Path
from typing import Any

from local_storage import conversation_store_path, ensure_layout

_LOCK = threading.RLock()
_SAFE_USER_ID = re.compile(r"^[A-Za-z0-9._-]+$")


def _store_path() -> Path:
    ensure_layout()
    return conversation_store_path()


def sync_configured() -> bool:
    return bool(os.getenv("RESEARCH_OS_SYNC_KEY", "").strip())


def authorize(candidate: str | None) -> bool:
    expected = os.getenv("RESEARCH_OS_SYNC_KEY", "").strip()
    if not expected or not candidate:
        return False
    return secrets.compare_digest(expected, candidate.strip())


def _validate_user_id(user_id: str) -> str:
    value = str(user_id or "").strip()
    if not value or not _SAFE_USER_ID.fullmatch(value) or value in {".", ".."}:
        raise ValueError("invalid user_id")
    return value[:128]


def _read_all() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"sessions": {}, "users": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}, "users": {}}
    if not isinstance(value, dict):
        return {"sessions": {}, "users": {}}
    if not isinstance(value.get("sessions"), dict):
        value["sessions"] = {}
    if not isinstance(value.get("users"), dict):
        value["users"] = {}
    return value


def _write_all(value: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _user_sessions(value: dict[str, Any], user_id: str) -> dict[str, Any]:
    users = value.setdefault("users", {})
    bucket = users.setdefault(user_id, {})
    if not isinstance(bucket, dict):
        bucket = {}
        users[user_id] = bucket
    sessions = bucket.setdefault("sessions", {})
    if not isinstance(sessions, dict):
        sessions = {}
        bucket["sessions"] = sessions
    return sessions


def list_sessions(user_id: str | None = None) -> list[dict[str, Any]]:
    """List sessions, optionally scoped to one verified user.

    ``user_id=None`` is retained for local/legacy callers only. Cloud routes
    must always pass the verified Research OS principal id.
    """
    with _LOCK:
        value = _read_all()
        if user_id is None:
            sessions = value["sessions"]
        else:
            sessions = _user_sessions(value, _validate_user_id(user_id))
        values = [item for item in sessions.values() if isinstance(item, dict)]
        values.sort(key=lambda item: int(item.get("updated_at", 0)), reverse=True)
        return values


def upsert_session(session: dict[str, Any], user_id: str | None = None) -> dict[str, Any]:
    session_id = str(session.get("id", "")).strip()
    if not session_id:
        raise ValueError("session.id is required")
    title = str(session.get("title", "New conversation")).strip() or "New conversation"
    updated_at = int(session.get("updated_at", 0) or 0)
    raw_messages = session.get("messages", [])
    if not isinstance(raw_messages, list):
        raise ValueError("session.messages must be a list")

    messages: list[dict[str, Any]] = []
    for raw in raw_messages[-100:]:
        if not isinstance(raw, dict):
            continue
        role = str(raw.get("role", "")).strip()
        text = str(raw.get("text", "")).strip()
        if role not in {"user", "assistant"} or not text:
            continue
        item: dict[str, Any] = {"role": role, "text": text}
        memory_count = raw.get("memory_count")
        if isinstance(memory_count, int):
            item["memory_count"] = max(0, memory_count)
        messages.append(item)

    normalized = {
        "id": session_id[:128],
        "title": title[:160],
        "updated_at": updated_at,
        "messages": messages,
    }
    with _LOCK:
        value = _read_all()
        if user_id is None:
            value["sessions"][normalized["id"]] = normalized
        else:
            scoped_user = _validate_user_id(user_id)
            _user_sessions(value, scoped_user)[normalized["id"]] = normalized
        _write_all(value)
    return normalized


def delete_session(session_id: str, user_id: str | None = None) -> bool:
    session_id = session_id.strip()
    if not session_id:
        raise ValueError("session_id is required")
    with _LOCK:
        value = _read_all()
        if user_id is None:
            sessions = value["sessions"]
        else:
            sessions = _user_sessions(value, _validate_user_id(user_id))
        existed = sessions.pop(session_id, None) is not None
        if existed:
            _write_all(value)
        return existed
