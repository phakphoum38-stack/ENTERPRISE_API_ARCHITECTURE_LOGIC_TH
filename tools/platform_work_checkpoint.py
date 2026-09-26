#!/usr/bin/env python3
"""Persistent, compact Platform work checkpoints for Research OS continuity.

Checkpoints contain resumable state and provenance, not chat transcripts or model
reasoning. They are append-only records; a newer checkpoint supersedes an older
one. The store is local-first and becomes durable when RESEARCH_OS_DATA_DIR is
backed by durable storage.
"""
from __future__ import annotations

import json
import re
import secrets
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any

from tools.research_os_api.local_storage import data_root

ROOT = Path(__file__).resolve().parents[1]
_LOCK = threading.RLock()
_SAFE = re.compile(r"^[^\\x00-\\x1f\\x7f]{1,128}$")
_STATES = {"ACTIVE", "PAUSED", "BLOCKED", "DEFERRED", "COMPLETED"}
_MAX_ITEMS = 64
_MAX_TEXT = 512
_MAX_REFS = 64


def canonical_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def _store_path() -> Path:
    return data_root() / "platform" / "work_checkpoints.json"


def _validate_id(value: str, field: str) -> str:
    value = str(value or "").strip()
    if (not value or not _SAFE.fullmatch(value) or "/" in value or "\\\\" in value or value in {".", ".."}):
        raise ValueError(f"invalid {field}")
    return value


def _clean_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be an array")
    if len(value) > _MAX_ITEMS:
        raise ValueError(f"{field} exceeds {_MAX_ITEMS} items")
    result = []
    for item in value:
        text = str(item).strip()
        if not text or len(text) > _MAX_TEXT:
            raise ValueError(f"invalid {field} item")
        result.append(text)
    return list(dict.fromkeys(result))


def _read() -> dict[str, Any]:
    path = _store_path()
    if not path.exists():
        return {"version": 1, "checkpoints": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise ValueError("checkpoint store is unreadable")
    if not isinstance(value, dict) or not isinstance(value.get("checkpoints"), list):
        raise ValueError("checkpoint store is invalid")
    return value


def _write(value: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def create_checkpoint(
    *,
    owner_id: str,
    task_id: str,
    workflow_state: str,
    current_step: str,
    completed_steps: list[str] | None = None,
    pending_steps: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    deferred_work: list[str] | None = None,
    context_refs: list[str] | None = None,
    next_action: str = "recon",
    source_sha: str | None = None,
    supersedes: str | None = None,
) -> dict[str, Any]:
    owner = _validate_id(owner_id, "owner_id")
    task = _validate_id(task_id, "task_id")
    state = str(workflow_state or "").strip().upper()
    if state not in _STATES:
        raise ValueError("invalid workflow_state")
    step = str(current_step or "").strip()
    action = str(next_action or "").strip()
    if not step or len(step) > _MAX_TEXT or not action or len(action) > _MAX_TEXT:
        raise ValueError("current_step and next_action are required")
    refs = _clean_list(evidence_refs, "evidence_refs")
    if len(refs) > _MAX_REFS:
        raise ValueError("too many evidence_refs")
    record = {
        "checkpoint_id": "cp-" + uuid.uuid4().hex,
        "owner_id": owner,
        "task_id": task,
        "workflow_state": state,
        "current_step": step[:_MAX_TEXT],
        "completed_steps": _clean_list(completed_steps, "completed_steps"),
        "pending_steps": _clean_list(pending_steps, "pending_steps"),
        "evidence_refs": refs,
        "deferred_work": _clean_list(deferred_work, "deferred_work"),
        "context_refs": _clean_list(context_refs, "context_refs"),
        "next_action": action[:_MAX_TEXT],
        "source_sha": source_sha or canonical_sha(),
        "supersedes": _validate_id(supersedes, "supersedes") if supersedes else None,
        "created_at": int(time.time()),
    }
    with _LOCK:
        value = _read()
        value["checkpoints"].append(record)
        _write(value)
    return record


def list_checkpoints(owner_id: str, task_id: str | None = None) -> list[dict[str, Any]]:
    owner = _validate_id(owner_id, "owner_id")
    task = _validate_id(task_id, "task_id") if task_id else None
    with _LOCK:
        records = [
            item for item in _read()["checkpoints"]
            if isinstance(item, dict)
            and item.get("owner_id") == owner
            and (task is None or item.get("task_id") == task)
        ]
    records.sort(key=lambda item: int(item.get("created_at", 0)), reverse=True)
    return records


def get_checkpoint(owner_id: str, checkpoint_id: str) -> dict[str, Any]:
    checkpoint_id = _validate_id(checkpoint_id, "checkpoint_id")
    for item in list_checkpoints(owner_id):
        if item.get("checkpoint_id") == checkpoint_id:
            return item
    raise KeyError("checkpoint_not_found")


def resume_checkpoint(owner_id: str, checkpoint_id: str) -> dict[str, Any]:
    checkpoint = get_checkpoint(owner_id, checkpoint_id)
    current = canonical_sha()
    failures: list[str] = []
    if checkpoint.get("source_sha") != current:
        failures.append("source_sha_mismatch")
    if checkpoint.get("workflow_state") == "COMPLETED":
        failures.append("already_completed")
    if checkpoint.get("workflow_state") not in _STATES:
        failures.append("invalid_workflow_state")
    if checkpoint.get("supersedes"):
        try:
            parent = get_checkpoint(owner_id, str(checkpoint["supersedes"]))
        except KeyError:
            failures.append("missing_superseded_checkpoint")
        else:
            if parent.get("task_id") != checkpoint.get("task_id"):
                failures.append("superseded_task_mismatch")
    return {
        "status": "HOLD" if failures else "READY",
        "checkpoint": checkpoint,
        "current_sha": current,
        "failures": failures,
        "next_action": (
            "repair_checkpoint_then_reverify"
            if failures
            else checkpoint["next_action"]
        ),
    }


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("--owner", required=True)
    create.add_argument("--task", required=True)
    create.add_argument("--state", required=True)
    create.add_argument("--step", required=True)
    create.add_argument("--next-action", default="recon")
    resume = sub.add_parser("resume")
    resume.add_argument("--owner", required=True)
    resume.add_argument("--checkpoint", required=True)
    args = parser.parse_args()
    if args.command == "create":
        payload = create_checkpoint(
            owner_id=args.owner,
            task_id=args.task,
            workflow_state=args.state,
            current_step=args.step,
            next_action=args.next_action,
        )
    else:
        payload = resume_checkpoint(args.owner, args.checkpoint)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
