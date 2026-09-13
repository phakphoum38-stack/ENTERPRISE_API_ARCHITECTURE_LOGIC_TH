from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Sequence

from identity_context import IdentityContext
from memory import build_context, search_memory

ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = ROOT / "research" / "artifacts"
DEFAULT_GITHUB_REPOSITORY = "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH"
DEFAULT_CONTEXT_PATHS = ("README.md", "tools/research_os_api/README.md")
MAX_MESSAGE_CHARS = 8192
MAX_MESSAGES = 32
MAX_CONTEXT_FILES = 10
MAX_CONTEXT_FILE_BYTES = 4096
MAX_CONTEXT_TOTAL_BYTES = 16384
BLOCKED_CONTEXT_NAMES = {".env", ".env.local", ".env.production", ".env.development", "credentials.json", "service-account.json", "id_rsa", "id_ed25519"}
BLOCKED_CONTEXT_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".crt", ".cer"}
_ALLOWED_CHAT_FIELDS = {"context_query", "memory_limit", "message", "messages", "paths", "model", "system"}
_RESERVED_SCOPE_FIELDS = {"owner", "owner_id", "profile", "profile_id", "role", "session_id", "user_id"}
_AUDIT_LOCK = threading.Lock()

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.copilot_chat.client import CopilotChatClient, CopilotChatConfigError, CopilotChatError


def build_copilot_context(identity: IdentityContext, *, query: str = "", paths: Sequence[str] | None = None, memory_limit: int = 5) -> dict[str, Any]:
    requested = _normalize_paths(paths)
    selected = requested or list(DEFAULT_CONTEXT_PATHS)
    snapshots = [_snapshot_file(path) for path in selected]
    total = sum(int(item["size"]) for item in snapshots)
    if total > MAX_CONTEXT_TOTAL_BYTES:
        raise ValueError(f"requested context exceeds {MAX_CONTEXT_TOTAL_BYTES} byte limit")
    normalized_query = str(query or "").strip()
    if len(normalized_query) > MAX_MESSAGE_CHARS:
        raise ValueError(f"context query exceeds {MAX_MESSAGE_CHARS} character limit")
    hits = search_memory(ARTIFACT_DIR, normalized_query, max(1, int(memory_limit))) if normalized_query else []
    return {"repository": _repository_name(), "branch": _git_branch(), "scope": {"profile_id": identity.profile_id, "role": identity.role}, "files": snapshots, "memory_count": len(hits), "memory_hits": hits, "memory_summary": build_context(hits)}


def chat_with_copilot(identity: IdentityContext, payload: dict[str, Any]) -> dict[str, Any]:
    _validate_chat_payload(payload)
    messages = _normalize_messages(payload)
    last_user_message = next((str(item["content"]).strip() for item in reversed(messages) if item["role"] == "user" and str(item["content"]).strip()), "")
    if not last_user_message:
        raise ValueError("message is required")
    context = build_copilot_context(identity, query=str(payload.get("context_query") or last_user_message), paths=payload.get("paths"), memory_limit=normalize_memory_limit(payload.get("memory_limit", 5)))
    result = CopilotChatClient().chat(messages=messages, context=context, metadata={"repository": context["repository"], "profile_id": identity.profile_id, "session_hash": _stable_hash(identity.session_id)})
    audit_path = write_audit_record({"event":"copilot.chat","timestamp":datetime.now(timezone.utc).isoformat(),"repository":context["repository"],"branch":context["branch"],"profile_id":identity.profile_id,"user_hash":_stable_hash(identity.user_id),"session_hash":_stable_hash(identity.session_id),"requested_paths":[item["path"] for item in context["files"]],"message_count":len(messages),"memory_count":context["memory_count"],"prompt_hash":_stable_hash(last_user_message),"response_hash":_stable_hash(result["reply"]),"response_chars":len(result["reply"])})
    return {"provider":"copilot-chat","model":result["model"],"reply":result["reply"],"text":result["reply"],"context":context,"audit":{"written":True,"path":_display_path(audit_path)}}


def write_audit_record(record: dict[str, Any]) -> Path:
    directory = Path(os.getenv("RESEARCH_OS_COPILOT_AUDIT_DIR") or ROOT / "evidence" / "copilot_chat")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "audit.jsonl"
    with _AUDIT_LOCK:
        previous_hash = "GENESIS"
        if path.is_file():
            try:
                last = path.read_text(encoding="utf-8").splitlines()[-1]
                previous = json.loads(last)
                previous_hash = str(previous.get("event_hash") or "GENESIS")
            except (IndexError, OSError, UnicodeDecodeError, json.JSONDecodeError):
                raise CopilotChatError("Copilot audit ledger is malformed; refusing to append")
        payload = dict(record)
        payload["previous_event_hash"] = previous_hash
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload["event_hash"] = _stable_hash(canonical)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return path


def _normalize_messages(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw_messages = payload.get("messages")
    messages: list[dict[str, str]] = []
    if raw_messages is not None:
        if not isinstance(raw_messages, list) or len(raw_messages) > MAX_MESSAGES:
            raise ValueError(f"messages must contain at most {MAX_MESSAGES} entries")
        for item in raw_messages:
            if not isinstance(item, dict):
                raise ValueError("messages entries must be objects")
            role = _optional_text(item.get("role")) or "user"
            content = _optional_text(item.get("content")) or ""
            if role not in {"user", "assistant"}:
                raise ValueError("messages role must be user or assistant")
            if not content or len(content) > MAX_MESSAGE_CHARS:
                raise ValueError(f"message content must be between 1 and {MAX_MESSAGE_CHARS} characters")
            messages.append({"role": role, "content": content})
    if messages:
        return messages
    message = _optional_text(payload.get("message")) or ""
    if not message:
        raise ValueError("message is required")
    if len(message) > MAX_MESSAGE_CHARS:
        raise ValueError(f"message exceeds {MAX_MESSAGE_CHARS} character limit")
    return [{"role":"user","content":message}]


def _normalize_paths(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items: Iterable[Any] = value.split(",")
    elif isinstance(value, list):
        items = value
    else:
        raise ValueError("paths must be an array or comma-separated string")
    paths: list[str] = []
    for item in items:
        text = _optional_text(item)
        if not text:
            continue
        for part in text.split(","):
            normalized = _optional_text(part)
            if normalized:
                paths.append(normalized)
    if len(paths) > MAX_CONTEXT_FILES:
        raise ValueError(f"at most {MAX_CONTEXT_FILES} context paths are allowed")
    return paths


def _snapshot_file(raw_path: str) -> dict[str, Any]:
    relative = str(raw_path or "").strip().replace("\\", "/").lstrip("/")
    if not relative or any(part == ".." for part in Path(relative).parts):
        raise ValueError(f"invalid context path: {relative}")
    path_obj = Path(relative)
    lowered_name = path_obj.name.lower()
    if lowered_name in BLOCKED_CONTEXT_NAMES or any(lowered_name.endswith(suffix) for suffix in BLOCKED_CONTEXT_SUFFIXES) or lowered_name.startswith(".env."):
        raise ValueError(f"sensitive context path is not allowed: {relative}")
    candidate = ROOT / path_obj
    current = ROOT
    for part in path_obj.parts:
        current = current / part
        if current.exists() and current.is_symlink():
            raise ValueError(f"context symlinks are not allowed: {relative}")
    resolved = candidate.resolve()
    if ROOT not in resolved.parents and resolved != ROOT:
        raise ValueError(f"context path escapes repository root: {relative}")
    if not resolved.is_file():
        raise ValueError(f"context file does not exist: {relative}")
    size = resolved.stat().st_size
    if size > MAX_CONTEXT_FILE_BYTES:
        raise ValueError(f"context file exceeds {MAX_CONTEXT_FILE_BYTES} byte limit: {relative}")
    data = resolved.read_bytes()
    return {"path":relative,"content":data.decode("utf-8", errors="replace"),"truncated":False,"size":len(data)}


def _git_branch() -> str:
    try:
        result = subprocess.run(["git","rev-parse","--abbrev-ref","HEAD"],cwd=ROOT,check=True,capture_output=True,text=True)
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


def _repository_name() -> str:
    return str(os.getenv("RESEARCH_OS_GITHUB_REPOSITORY") or "").strip() or DEFAULT_GITHUB_REPOSITORY


def _optional_text(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def _stable_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_chat_payload(payload: dict[str, Any]) -> None:
    if not isinstance(payload, dict):
        raise ValueError("copilot chat payload must be an object")
    unexpected = sorted(set(payload) - _ALLOWED_CHAT_FIELDS - _RESERVED_SCOPE_FIELDS)
    if unexpected:
        raise ValueError("unsupported copilot chat fields: " + ", ".join(unexpected))
    forbidden = [key for key in _RESERVED_SCOPE_FIELDS if key in payload]
    if forbidden:
        raise ValueError("trusted user scope is derived from the Research OS session and cannot be overridden")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def normalize_memory_limit(value: Any) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("memory_limit must be an integer between 1 and 50") from exc
    if limit < 1 or limit > 50:
        raise ValueError("memory_limit must be between 1 and 50")
    return limit
