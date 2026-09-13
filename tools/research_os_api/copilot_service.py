from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from identity_context import IdentityContext
from memory import build_context, search_memory

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "research" / "artifacts"
DEFAULT_GITHUB_REPOSITORY = "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH"
DEFAULT_CONTEXT_PATHS = ("README.md", "tools/research_os_api/README.md")
_RESERVED_SCOPE_FIELDS = {
    "owner",
    "owner_id",
    "profile",
    "profile_id",
    "role",
    "session_id",
    "user_id",
}

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.copilot_chat.client import CopilotChatClient, CopilotChatError


def build_copilot_context(
    identity: IdentityContext,
    *,
    query: str = "",
    paths: Sequence[str] | None = None,
    memory_limit: int = 5,
) -> dict[str, Any]:
    requested = _normalize_paths(paths)
    snapshots = [_snapshot_file(path) for path in requested or DEFAULT_CONTEXT_PATHS]
    normalized_query = str(query or "").strip()
    hits = (
        search_memory(ARTIFACT_DIR, normalized_query, max(1, int(memory_limit)))
        if normalized_query
        else []
    )
    return {
        "repository": _repository_name(),
        "branch": _git_branch(),
        "scope": {
            "profile_id": identity.profile_id,
            "role": identity.role,
        },
        "files": snapshots,
        "memory_count": len(hits),
        "memory_hits": hits,
        "memory_summary": build_context(hits),
    }


def chat_with_copilot(
    identity: IdentityContext,
    payload: dict[str, Any],
) -> dict[str, Any]:
    _validate_scope_payload(payload)
    messages = _normalize_messages(payload)
    last_user_message = next(
        (
            str(item["content"]).strip()
            for item in reversed(messages)
            if item["role"] == "user" and str(item["content"]).strip()
        ),
        "",
    )
    if not last_user_message:
        raise ValueError("message is required")
    context = build_copilot_context(
        identity,
        query=str(payload.get("context_query") or last_user_message),
        paths=payload.get("paths"),
        memory_limit=int(payload.get("memory_limit", 5)),
    )
    result = CopilotChatClient().chat(
        messages=messages,
        context=context,
        metadata={
            "repository": context["repository"],
            "profile_id": identity.profile_id,
            "session_id": identity.session_id,
        },
        model=_optional_text(payload.get("model")),
    )
    audit_path = write_audit_record(
        {
            "event": "copilot.chat",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repository": context["repository"],
            "branch": context["branch"],
            "profile_id": identity.profile_id,
            "user_hash": _stable_hash(identity.user_id),
            "session_hash": _stable_hash(identity.session_id),
            "requested_paths": [item["path"] for item in context["files"]],
            "message_count": len(messages),
            "memory_count": context["memory_count"],
            "prompt_hash": _stable_hash(last_user_message),
            "response_hash": _stable_hash(result["reply"]),
            "response_chars": len(result["reply"]),
        }
    )
    return {
        "provider": "copilot-chat",
        "model": result["model"],
        "reply": result["reply"],
        "text": result["reply"],
        "context": context,
        "audit": {"written": True, "path": _display_path(audit_path)},
    }


def write_audit_record(record: dict[str, Any]) -> Path:
    directory = Path(
        os.getenv("RESEARCH_OS_COPILOT_AUDIT_DIR")
        or ROOT / "evidence" / "copilot_chat"
    )
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "audit.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _normalize_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw_messages = payload.get("messages")
    messages: list[dict[str, str]] = []
    if isinstance(raw_messages, list):
        for item in raw_messages:
            if not isinstance(item, dict):
                raise ValueError("messages entries must be objects")
            role = _optional_text(item.get("role")) or "user"
            content = _optional_text(item.get("content")) or ""
            if not content:
                continue
            if role not in {"system", "user", "assistant"}:
                raise ValueError("messages role must be system, user, or assistant")
            messages.append({"role": role, "content": content})
    if messages:
        return messages
    message = _optional_text(payload.get("message")) or ""
    if not message:
        raise ValueError("message is required")
    system = _optional_text(payload.get("system"))
    normalized = [{"role": "user", "content": message}]
    if system:
        normalized.insert(0, {"role": "system", "content": system})
    return normalized


def _normalize_paths(value: Any) -> list[str]:
    if value is None:
        return []
    items: Iterable[Any]
    if isinstance(value, str):
        items = value.split(",")
    elif isinstance(value, list):
        items = value
    else:
        raise ValueError("paths must be an array or comma-separated string")
    paths: list[str] = []
    for item in items:
        text = _optional_text(item)
        if not text:
            continue
        paths.append(text)
    return paths[:10]


def _snapshot_file(raw_path: str) -> dict[str, Any]:
    relative = str(raw_path or "").strip().replace("\\", "/").lstrip("/")
    if not relative:
        raise ValueError("context path cannot be empty")
    resolved = (ROOT / relative).resolve()
    if ROOT not in resolved.parents and resolved != ROOT:
        raise ValueError(f"context path escapes repository root: {relative}")
    if not resolved.is_file():
        raise ValueError(f"context file does not exist: {relative}")
    data = resolved.read_bytes()
    text = data[:4096].decode("utf-8", errors="replace")
    truncated = len(data) > 4096
    return {
        "path": relative,
        "content": text,
        "truncated": truncated,
        "size": len(data),
    }


def _git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _repository_name() -> str:
    return (
        str(os.getenv("RESEARCH_OS_GITHUB_REPOSITORY") or "").strip()
        or DEFAULT_GITHUB_REPOSITORY
    )


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_scope_payload(payload: dict[str, Any]) -> None:
    forbidden = [
        key
        for key in _RESERVED_SCOPE_FIELDS
        if key in payload and _optional_text(payload.get(key))
    ]
    if forbidden:
        raise ValueError(
            "trusted user scope is derived from the Research OS session and cannot be overridden"
        )


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)
