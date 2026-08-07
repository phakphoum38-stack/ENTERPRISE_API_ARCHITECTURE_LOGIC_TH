#!/usr/bin/env python3
"""Small authenticated conversation store for Research OS cloud sync.

The default JSON backend is intentionally simple and dependency-free. On Render
free instances it is suitable for cross-device sync while the instance exists,
but the filesystem is ephemeral across replacement/deploys. The storage API is
kept isolated so a durable Redis/Postgres adapter can replace it without changing
Flutter endpoints.
"""

from __future__ import annotations

import json
import os
import secrets
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.RLock()


def _store_path() -> Path:
    return Path(os.getenv("RESEARCH_OS_CONVERSATION_STORE", "/tmp/research_os_conversations.json"))


def sync_configured() -> bool:
    return bool(os.getenv("RESEARCH_OS_SYNC_KEY", "").strip())


def authorize(candidate: str | None) -> bool:
    expected = os.getenv("RESEARCH_OS_SYNC_KEY", "").strip()
    if not expected or not candidate:
        return False
    return secrets.compare_digest(expected, candidate.strip())


def _read_all() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"sessions": {}}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"sessions": {}}
    if not isinstance(value, dict):
        return {"sessions": {}}
    sessions = value.get("sessions")
    if not isinstance(sessions, dict):
        value["sessions"] = {}
    return value


def _write_all(value: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def list_sessions() -> list[dict[str, Any]]:
    with _LOCK:
        sessions = _read_all()["sessions"]
        values = [item for item in sessions.values() if isinstance(item, dict)]
        values.sort(key=lambda item: int(item.get("updated_at", 0)), reverse=True)
        return values


def upsert_session(session: dict[str, Any]) -> dict[str, Any]:
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
        value["sessions"][normalized["id"]] = normalized
        _write_all(value)
    return normalized


def delete_session(session_id: str) -> bool:
    session_id = session_id.strip()
    if not session_id:
        raise ValueError("session_id is required")
    with _LOCK:
        value = _read_all()
        existed = value["sessions"].pop(session_id, None) is not None
        if existed:
            _write_all(value)
        return existed
