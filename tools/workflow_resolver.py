#!/usr/bin/env python3
"""Canonical, side-effect-free binding from Control Center commands to workflows.

The resolver deliberately stops before execution. It turns an already prepared
CommandSpec into an immutable execution plan that an existing workflow/executor
adapter can consume. No GitHub API, subprocess, queue, scheduler, or authority
system is created here.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from universal_control_surface import CommandSpec


WORKFLOW_DISPATCH = "workflow_dispatch"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class WorkflowTarget:
    file: str
    stage: int
    role: str
    dispatchable: bool


@dataclass(frozen=True)
class ResolvedWorkflow:
    command_id: str
    command_fingerprint: str
    workflow: WorkflowTarget
    workflow_name: str
    dispatch_endpoint: str
    target_sha: str | None
    input_keys: tuple[str, ...]
    resolution_fingerprint: str


class WorkflowResolutionError(ValueError):
    """Fail-closed error raised when a command cannot bind uniquely."""


def _norm(value: str) -> str:
    return " ".join(value.strip().lower().replace("_", "-").split())


def _workflow_file(value: str) -> str:
    value = value.strip().replace("\\", "/")
    return value.rsplit("/", 1)[-1]


def command_fingerprint(command: CommandSpec) -> str:
    payload = {
        "command_id": command.command_id,
        "label": command.label,
        "intent": command.intent,
        "target": command.target,
        "mode": command.mode,
        "risk": command.risk,
        "keywords": list(command.keywords),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def resolve_workflow(
    command: CommandSpec,
    registry: Mapping[str, Any],
    *,
    workflow_source: str,
    target_sha: str | None = None,
) -> ResolvedWorkflow:
    """Resolve a command to one existing workflow without executing it.

    Matching is intentionally deterministic and fail-closed. The target may
    identify an exact workflow file, its registry role, or its declared name.
    Ambiguous or missing matches are rejected.
    """
    target = _norm(command.target)
    if not target:
        raise WorkflowResolutionError("workflow target is required")

    stages = registry.get("stages")
    if not isinstance(stages, Sequence) or isinstance(stages, (str, bytes)):
        raise WorkflowResolutionError("registry stages are missing or invalid")

    candidates: list[WorkflowTarget] = []
    for raw in stages:
        if not isinstance(raw, Mapping):
            continue
        file = str(raw.get("file") or "").strip()
        role = str(raw.get("role") or "").strip()
        if not file or not role:
            continue
        stage = int(raw.get("stage", -1))
        dispatchable = raw.get("dispatchable") is True
        names = {_norm(file), _norm(_workflow_file(file)), _norm(role)}
        if target in names:
            candidates.append(WorkflowTarget(file, stage, role, dispatchable))

    # The workflow's human-readable name is authoritative when the target is
    # phrased as "Run Generate Orchestrator" rather than a registry key.
    declared_name = _declared_workflow_name(workflow_source)
    if declared_name and _norm(declared_name) == target.removeprefix("run "):
        for raw in stages:
            if not isinstance(raw, Mapping):
                continue
            file = str(raw.get("file") or "").strip()
            if file and _norm(_workflow_file(file)) == _norm(_workflow_file_from_source(declared_name, stages)):
                role = str(raw.get("role") or "").strip()
                candidates.append(WorkflowTarget(file, int(raw.get("stage", -1)), role, raw.get("dispatchable") is True))

    unique = {(c.file, c.stage, c.role, c.dispatchable): c for c in candidates}
    candidates = list(unique.values())
    if len(candidates) != 1:
        raise WorkflowResolutionError(
            f"workflow target must resolve to exactly one existing workflow; got {len(candidates)}"
        )

    workflow = candidates[0]
    if WORKFLOW_DISPATCH not in workflow_source:
        raise WorkflowResolutionError(
            f"workflow {workflow.file} does not declare workflow_dispatch"
        )

    if target_sha is not None and not SHA256_RE.fullmatch(target_sha):
        raise WorkflowResolutionError("target_sha must be a canonical 64-character SHA-256 value")

    # Non-dispatchable means "not a downstream stage". The canonical
    # orchestrator is intentionally non-dispatchable in its own registry to
    # prevent recursive downstream dispatch; direct Control Center binding is
    # still allowed when the workflow itself declares workflow_dispatch.
    payload = {
        "command_id": command.command_id,
        "command_fingerprint": command_fingerprint(command),
        "workflow_file": workflow.file,
        "stage": workflow.stage,
        "role": workflow.role,
        "workflow_name": declared_name or "",
        "target_sha": target_sha,
        "input_keys": tuple(sorted(_dispatch_input_keys(workflow_source))),
    }
    resolution_fingerprint = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

    return ResolvedWorkflow(
        command_id=command.command_id,
        command_fingerprint=payload["command_fingerprint"],
        workflow=workflow,
        workflow_name=declared_name or workflow.file,
        dispatch_endpoint=f"/actions/workflows/{_workflow_file(workflow.file)}/dispatches",
        target_sha=target_sha,
        input_keys=payload["input_keys"],
        resolution_fingerprint=resolution_fingerprint,
    )


def _declared_workflow_name(source: str) -> str:
    for line in source.splitlines():
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return ""


def _dispatch_input_keys(source: str) -> set[str]:
    keys: set[str] = set()
    in_dispatch = False
    in_inputs = False
    dispatch_indent = 0
    inputs_indent = 0
    for line in source.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        if stripped == "workflow_dispatch:":
            in_dispatch = True
            dispatch_indent = indent
            in_inputs = False
            continue
        if in_dispatch and indent <= dispatch_indent and not stripped.startswith("workflow_dispatch"):
            in_dispatch = False
            in_inputs = False
        if in_dispatch and stripped == "inputs:":
            in_inputs = True
            inputs_indent = indent
            continue
        if in_inputs:
            if indent <= inputs_indent:
                in_inputs = False
                continue
            if indent == inputs_indent + 2 and stripped.endswith(":"):
                keys.add(stripped[:-1].strip())
    return keys


def _workflow_file_from_source(declared_name: str, stages: Sequence[Any]) -> str:
    # Prefer the registry's file whose human-readable role/name contains the
    # declared workflow name; this helper only participates in name matching.
    wanted = _norm(declared_name)
    for raw in stages:
        if not isinstance(raw, Mapping):
            continue
        file = str(raw.get("file") or "").strip()
        role = str(raw.get("role") or "").strip()
        if wanted in {_norm(file), _norm(_workflow_file(file)), _norm(role)}:
            return file
    return declared_name
