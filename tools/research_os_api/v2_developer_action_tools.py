#!/usr/bin/env python3
"""Approval-gated workspace mutations and controlled commands (Brain Phase 6)."""
from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from v2_tool_registry import ToolDefinition, ToolRegistry
from v2_workspace_tools import WorkspaceBoundaryError, WorkspaceReadTools

CONTRACT = "brain-developer-actions-phase-6"
_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{2,63}$")
MAX_FILE = 1024 * 1024
MAX_DIFF = 32 * 1024
MAX_OUTPUT = 64 * 1024

TOOLS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        "workspace.file.change", "1.0.0", "Workspace File Change",
        "Preview and apply bounded UTF-8 file writes/replacements inside one workspace sandbox.",
        ("workspace_file_write", "workspace_file_edit", "workspace_file_patch", "workspace_diff_preview"),
        permissions=("workspace.read", "workspace.write"), mutating=True,
        idempotent=True, supports_dry_run=True,
    ),
    ToolDefinition(
        "workspace.command.run", "1.0.0", "Controlled Workspace Command",
        "Preview and execute a trusted host-defined test/build command profile without shell parsing.",
        ("controlled_command_execution", "test_execution", "build_execution"),
        permissions=("workspace.execute",), mutating=True, idempotent=False,
        supports_dry_run=True,
    ),
)
DEVELOPER_ACTION_TOOL_DEFINITIONS = TOOLS
DEVELOPER_ACTION_TOOLS_CONTRACT = CONTRACT


@dataclass(frozen=True)
class CommandProfile:
    command_id: str
    argv: tuple[str, ...]
    cwd: str = "."
    timeout_seconds: int = 120
    category: str = "test"

    def __post_init__(self) -> None:
        if not _ID_RE.fullmatch(self.command_id):
            raise ValueError(f"invalid command_id: {self.command_id}")
        if not self.argv or len(self.argv) > 32 or not all(isinstance(x, str) and x for x in self.argv):
            raise ValueError("command profile requires 1-32 fixed argv items")
        cwd = Path(self.cwd)
        if cwd.is_absolute() or ".." in cwd.parts:
            raise ValueError("command profile cwd must stay inside workspace")
        if not 1 <= self.timeout_seconds <= 600:
            raise ValueError("command timeout must be between 1 and 600 seconds")
        if self.category not in {"test", "build", "analyze", "verify"}:
            raise ValueError("command category must be test/build/analyze/verify")


CommandExecutor = Callable[[CommandProfile, Path, Mapping[str, str]], Mapping[str, Any]]


def _safe_env() -> dict[str, str]:
    keep = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP", "HOME", "USERPROFILE", "LANG", "LC_ALL"}
    env = {k: v for k, v in os.environ.items() if k.upper() in keep}
    env.update({"CI": "1", "RESEARCH_OS_COMMAND_SANDBOX": "1"})
    return env


def _run(profile: CommandProfile, cwd: Path, env: Mapping[str, str]) -> Mapping[str, Any]:
    p = subprocess.run(list(profile.argv), cwd=str(cwd), env=dict(env), shell=False,
                       check=False, capture_output=True, text=True, timeout=profile.timeout_seconds)
    out, err = p.stdout or "", p.stderr or ""
    out = out if len(out) <= MAX_OUTPUT else out[:MAX_OUTPUT - 3] + "..."
    err = err if len(err) <= MAX_OUTPUT else err[:MAX_OUTPUT - 3] + "..."
    if p.returncode:
        tail = err.strip()[-1200:] or out.strip()[-1200:]
        raise RuntimeError(f"controlled command failed with exit code {p.returncode}" + (f": {tail}" if tail else ""))
    return {"returncode": p.returncode, "stdout": out, "stderr": err}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fingerprint(path: str, action: str, before: str | None, after: str) -> str:
    raw = json.dumps({"path": path, "action": action, "before_sha256": before, "after_sha256": after},
                     sort_keys=True, separators=(",", ":")).encode()
    return _sha(raw)


class DeveloperActionTools:
    def __init__(self, workspace_root: str | os.PathLike[str], *,
                 command_profiles: Iterable[CommandProfile] = (),
                 command_executor: CommandExecutor = _run,
                 max_file_bytes: int = MAX_FILE, max_diff_chars: int = MAX_DIFF) -> None:
        if not 1024 <= max_file_bytes <= 2 * MAX_FILE:
            raise ValueError("max_file_bytes must be between 1 KiB and 2 MiB")
        if not 1024 <= max_diff_chars <= 256 * 1024:
            raise ValueError("max_diff_chars must be between 1 KiB and 256 KiB")
        if not callable(command_executor):
            raise ValueError("command_executor must be callable")
        self.workspace = WorkspaceReadTools(workspace_root, max_read_bytes=max_file_bytes)
        self.root, self.max_file, self.max_diff = self.workspace.root, max_file_bytes, max_diff_chars
        self.executor = command_executor
        self.profiles: dict[str, CommandProfile] = {}
        for p in command_profiles:
            if p.command_id in self.profiles:
                raise ValueError(f"duplicate command profile: {p.command_id}")
            if not self.workspace.resolve(p.cwd).is_dir():
                raise ValueError(f"command profile cwd is not a directory: {p.command_id}")
            self.profiles[p.command_id] = p

    def _target(self, value: Any) -> tuple[Path, str]:
        raw = str(value or "").strip()
        if not raw:
            raise ValueError("path is required")
        target = self.workspace.resolve(raw, must_exist=False)
        if (self.root / Path(raw)).is_symlink():
            raise WorkspaceBoundaryError("workspace file change does not modify symlinks")
        if target.exists() and not target.is_file():
            raise ValueError("workspace file change target must be a file")
        parent = target.parent.resolve(strict=True)
        try:
            parent.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceBoundaryError("target parent escapes configured workspace") from exc
        return target, target.relative_to(self.root).as_posix()

    def _current(self, target: Path) -> tuple[bytes, str]:
        if not target.exists():
            return b"", ""
        data = target.read_bytes()
        if len(data) > self.max_file:
            raise ValueError("existing file exceeds change limit")
        if b"\x00" in data:
            raise ValueError("binary files cannot be changed")
        try:
            return data, data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("workspace file change requires UTF-8 text") from exc

    @staticmethod
    def _proposed(action: str, current: str, payload: Mapping[str, Any]) -> str:
        if action == "write":
            value = payload.get("content")
            if not isinstance(value, str):
                raise ValueError("write action requires string content")
            return value
        if action == "replace":
            find, replacement = payload.get("find"), payload.get("replace")
            if not isinstance(find, str) or not find or not isinstance(replacement, str):
                raise ValueError("replace action requires find and replace strings")
            expected = int(payload.get("expected_occurrences", 1))
            actual = current.count(find)
            if not 1 <= expected <= 100 or actual != expected:
                raise ValueError(f"replace occurrence mismatch: expected {expected}, found {actual}")
            return current.replace(find, replacement, expected)
        raise ValueError(f"unsupported workspace.file.change action: {action}")

    def _preview(self, action: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        target, rel = self._target(payload.get("path"))
        existed = target.exists()
        before_b, before = self._current(target)
        after = self._proposed(action, before, payload)
        after_b = after.encode()
        if len(after_b) > self.max_file:
            raise ValueError("proposed file exceeds change limit")
        diff = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                            fromfile=f"a/{rel}", tofile=f"b/{rel}", n=3))
        truncated = len(diff) > self.max_diff
        diff = diff if not truncated else diff[:self.max_diff - 3] + "..."
        before_sha = _sha(before_b) if existed else None
        after_sha = _sha(after_b)
        return {
            "contract": CONTRACT, "path": rel, "action": action, "exists_before": existed,
            "before_sha256": before_sha, "after_sha256": after_sha,
            "changed": before_b != after_b, "diff": diff, "diff_truncated": truncated,
            "approval_fingerprint": _fingerprint(rel, action, before_sha, after_sha),
            "approval_binding": "path+action+before_sha256+after_sha256",
            "rollback_contract": "fresh_reverse_preview_and_approval", "applied": False,
        }

    def file_change(self, action: str, payload: Mapping[str, Any], *, dry_run: bool) -> dict[str, Any]:
        preview = self._preview(action, payload)
        if dry_run:
            return preview
        supplied = str(payload.get("approval_fingerprint") or "").strip()
        if not supplied:
            raise ValueError("approved apply requires approval_fingerprint from a fresh dry-run preview")
        if supplied != preview["approval_fingerprint"]:
            raise ValueError("approval_fingerprint mismatch; workspace state or proposed change has drifted")
        if not preview["changed"]:
            return {**preview, "applied": True, "no_op": True,
                    "verification": {"after_sha256": preview["after_sha256"], "matches": True}}
        target, _ = self._target(payload.get("path"))
        before_b, current = self._current(target)
        current_sha = _sha(before_b) if target.exists() else None
        if current_sha != preview["before_sha256"]:
            raise ValueError("workspace changed after approval fingerprint verification")
        data = self._proposed(action, current, payload).encode()
        mode = target.stat().st_mode if target.exists() else None
        tmp: str | None = None
        try:
            with tempfile.NamedTemporaryFile("wb", dir=str(target.parent), prefix=".research-os-change-", delete=False) as f:
                tmp = f.name; f.write(data); f.flush(); os.fsync(f.fileno())
            if mode is not None:
                os.chmod(tmp, mode)
            os.replace(tmp, target); tmp = None
        finally:
            if tmp:
                try: os.unlink(tmp)
                except OSError: pass
        actual = _sha(target.read_bytes())
        if actual != preview["after_sha256"]:
            raise RuntimeError("post-write verification hash mismatch")
        return {**preview, "applied": True, "no_op": False,
                "verification": {"after_sha256": actual, "matches": True}}

    def command_run(self, payload: Mapping[str, Any], *, dry_run: bool) -> dict[str, Any]:
        cid = str(payload.get("command_id") or "").strip()
        if cid not in self.profiles:
            raise ValueError(f"unknown controlled command profile: {cid}")
        p = self.profiles[cid]; cwd = self.workspace.resolve(p.cwd)
        plan = {"contract": CONTRACT, "command_id": cid, "category": p.category, "argv": list(p.argv),
                "cwd": cwd.relative_to(self.root).as_posix() or ".", "timeout_seconds": p.timeout_seconds,
                "shell": False, "network_credentials_inherited": False, "dry_run": dry_run}
        if dry_run:
            return {**plan, "executed": False}
        out = self.executor(p, cwd, _safe_env())
        if not isinstance(out, Mapping):
            raise TypeError("controlled command executor must return a mapping")
        return {**plan, "executed": True, "output": dict(out)}

    def adapter(self, tool_id: str):
        if tool_id == "workspace.file.change":
            return lambda action, payload, dry_run: self.file_change(action, payload, dry_run=dry_run)
        if tool_id == "workspace.command.run":
            def run(action: str, payload: Mapping[str, Any], dry_run: bool):
                if action != "run": raise ValueError(f"unsupported workspace.command.run action: {action}")
                return self.command_run(payload, dry_run=dry_run)
            return run
        raise ValueError(f"unsupported developer action tool: {tool_id}")

    def status(self) -> dict[str, Any]:
        return {"contract": CONTRACT, "tool_count": len(TOOLS), "arbitrary_shell": False,
                "command_profiles": sorted(self.profiles), "real_mutations_require_controller_approval": True,
                "approval_fingerprint_required": True, "network": False}


def install_developer_action_tools(registry: ToolRegistry, workspace_root: str | os.PathLike[str], *,
                                   command_profiles: Iterable[CommandProfile] = (),
                                   command_executor: CommandExecutor = _run,
                                   max_file_bytes: int = MAX_FILE,
                                   max_diff_chars: int = MAX_DIFF) -> DeveloperActionTools:
    pack = DeveloperActionTools(workspace_root, command_profiles=command_profiles,
                                command_executor=command_executor, max_file_bytes=max_file_bytes,
                                max_diff_chars=max_diff_chars)
    for d in TOOLS:
        try: existing = registry.get(d.tool_id)
        except ValueError: registry.register(d)
        else:
            if asdict(existing) != asdict(d): raise ValueError(f"developer action tool definition collision: {d.tool_id}")
        try: registry.register_adapter(d.tool_id, pack.adapter(d.tool_id))
        except ValueError as exc:
            if "already registered" not in str(exc): raise
            registry.register_adapter(d.tool_id, pack.adapter(d.tool_id), replace=True)
    return pack
