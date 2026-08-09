#!/usr/bin/env python3
"""V2 observability primitives built on existing Research OS runtime owners."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any

from agent_platform import REGISTRY
from agent_runtime import RUNTIME
from provider_readiness import inspect_all

_SECRET_MARKERS = ("key", "token", "secret", "password", "authorization", "credential")


def correlation_id(value: str | None = None) -> str:
    candidate = (value or "").strip()
    return candidate or str(uuid.uuid4())


def redact(value: Any) -> Any:
    """Recursively remove likely secret values while keeping diagnostic shape."""
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = str(key).casefold()
            result[str(key)] = "[REDACTED]" if any(marker in normalized for marker in _SECRET_MARKERS) else redact(item)
        return result
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, tuple):
        return [redact(item) for item in value]
    return value


def storage_readiness(data_dir: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    root = Path(data_dir or os.environ.get("RESEARCH_OS_DATA_DIR") or Path.home() / "ResearchOSData")
    try:
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".v2-readiness-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return {"ready": True, "path": str(root), "writable": True}
    except OSError as exc:
        return {"ready": False, "path": str(root), "writable": False, "error": type(exc).__name__}


def readiness_snapshot(data_dir: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    agents = REGISTRY.readiness()
    providers = inspect_all()
    active = str(providers["active"]).lower()
    active_provider = next(
        (item for item in providers["providers"] if item["provider"] == active),
        {"provider": active, "ready": False, "missing": ["unsupported_active_provider"]},
    )
    storage = storage_readiness(data_dir)
    runtime = RUNTIME.dashboard()
    overall = bool(agents["ready"] and active_provider["ready"] and storage["ready"])
    return redact(
        {
            "version": "2.0",
            "ready": overall,
            "runtime": {
                "task_queue": runtime["task_queue"],
                "event_bus": runtime["event_bus"],
                "shared_context": runtime["shared_context"],
                "task_count": runtime["task_count"],
            },
            "agents": agents,
            "provider": active_provider,
            "storage": storage,
            "checked_at": time.time(),
        }
    )


def structured_event(
    event_type: str,
    *,
    correlation: str | None = None,
    run_id: str | None = None,
    task_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return redact(
        {
            "timestamp": time.time(),
            "event_type": event_type,
            "correlation_id": correlation_id(correlation),
            "run_id": run_id,
            "task_id": task_id,
            "detail": detail or {},
        }
    )


def diagnostics_bundle(data_dir: str | os.PathLike[str] | None = None) -> dict[str, Any]:
    """Return a local, secret-redacted support bundle without exporting raw secrets."""
    return {
        "schema_version": 1,
        "generated_at": time.time(),
        "readiness": readiness_snapshot(data_dir),
        "environment": redact(
            {
                key: value
                for key, value in os.environ.items()
                if key.startswith("RESEARCH_OS_")
            }
        ),
        "recent_runtime_events": redact(RUNTIME.events.list(limit=50)),
    }


def write_diagnostics_bundle(
    target: str | os.PathLike[str],
    data_dir: str | os.PathLike[str] | None = None,
) -> Path:
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(diagnostics_bundle(data_dir), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


__all__ = [
    "correlation_id",
    "diagnostics_bundle",
    "readiness_snapshot",
    "redact",
    "storage_readiness",
    "structured_event",
    "write_diagnostics_bundle",
]
