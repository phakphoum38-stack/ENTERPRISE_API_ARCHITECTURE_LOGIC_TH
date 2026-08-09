#!/usr/bin/env python3
"""Governed developer actions for Research OS AI Brain.

Phase 6 adds opt-in workspace mutation and controlled test/build execution.
Every real mutation still passes through the Phase 4 HardenedExecutionController,
which requires permissions plus explicit approval. File changes are bound to a
dry-run change token so the approved bytes/path/current-state cannot drift
silently between preview and apply. Command execution accepts trusted command
profiles only; payloads never supply arbitrary shell strings or argv.
"""

from __future__ import annotations

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


DEVELOPER_ACTION_TOOLS_CONTRACT = "brain-developer-actions-phase-6"
_COMMAND_ID_RE = re.compile(r"^[a-z][a-z0-9_.-]{2,63}$")
_MAX_FILE_BYTES = 1024 * 1024
_MAX_DIFF_CHARS = 32 * 1024
_MAX_OUTPUT_CHARS = 64 * 1024


DEVELOPER_ACTION_TOOL_DEFINITIONS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        "workspace.file.change",
        "1.0.0",
        "Workspace File Change",
        "Preview and apply bounded UTF-8 file writes/replacements inside one workspace sandbox.",
        (
            "workspace_file_write",
            "workspace_file_edit",
            "workspace_file_patch",
            "workspace_diff_preview",
        ),
        permissions=("workspace.read", "workspace.write"),
        mutating=True,
        destructive=False,
        network=False,
        secret_access=False,
        idempotent=True,
        supports_dry_run=True,
    ),
    ToolDefinition(
        "workspace.command.run",
        "1.0.0",
        "Controlled Workspace Command",
        "Preview and execute a trusted host-defined test/build command profile without shell parsing.",
        ("controlled_command_execution", "test_execution", "build_execution"),
        permissions=("workspace.execute",),
        mutating=True,
        destructive=False,
        network=False,
        secret_access=False,
        idempotent=False,
        supports_dry_run=True,
    ),
)


@dataclass(frozen=True)
class CommandProfile:
    command_id: str
    argv: tuple[str, ...]
    cwd: str = "."
    timeout_seconds: int = 120
    category: str = "test"

    def __post_init__(self) -> None:
        if not _COMMAND_ID_RE.fullmatch(self.command_id):
            raise ValueError(f"invalid command_id: {self.command_id}")
        if not self.argv or not all(isinstance(item, str) and item for item in self.argv):
            raise ValueError(f"argv is required for command profile: {self.command_id}")
        if len(self.argv) > 32:
            raise ValueError("command profile argv is too long")
        raw_cwd = Path(self.cwd)
        if raw_cwd.is_absolute() or ".." in raw_cwd.parts:
            raise ValueError("command profile cwd must stay inside workspace")
        if self.timeout_seconds < 1 or self.timeout_seconds > 600:
            raise ValueError("command timeout must be between 1 and 600 seconds")
        if self.category not in {"test", "build", "analyze", "verify"}:
            raise ValueError("command category must be test/build/analyze/verify")


CommandExecutor = Callable[[CommandProfile, Path, Mapping[str, str]], Mapping[str, Any]]


def _safe_environment() -> dict[str, str]:
    allowed = {
        "PATH",
        "SYSTEMROOT",
        "WINDIR",
        "COMSPEC",
        "PATHEXT",
        "TEMP",
        "TMP",
        "HOME",
        "USERPROFILE",
        "LANG",
        "LC_ALL",
    }
    env = {key: value for key, value in os.environ.items() if key.upper() in allowed}
    env["CI"] = "1"
    env["RESEARCH_OS_COMMAND_SANDBOX"] = "1"
    return env


def _subprocess_executor(
    profile: CommandProfile,
    cwd: Path,
    env: Mapping[str, str],
) -> Mapping[str, Any]:
    completed = subprocess.run(
        list(profile.argv),
        cwd=str(cwd),
        env=dict(env),
        shell=False,
        check=False,
        capture_output=True,
        text=True,
        timeout=profile.timeout_seconds,
    )
    stdout = completed.stdout or ""
    stderr = completed.stderr or ""
    if len(stdout) > _MAX_OUTPUT_CHARS:
        stdout = stdout[: _MAX_OUTPUT_CHARS - 3] + "..."
    if len(stderr) > _MAX_OUTPUT_CHARS:
        stderr = stderr[: _MAX_OUTPUT_CHARS - 3] + "..."
    if completed.returncode != 0:
        tail = stderr.strip()[-1200:] or stdout.strip()[-1200:]
        raise RuntimeError(
            f"controlled command failed with exit code {completed.returncode}"
            + (f": {tail}" if tail else "")
        )
    return {"returncode": completed.returncode, "stdout": stdout, "stderr": stderr}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _change_token(
    *,
    path: str,
    action: str,
    before_sha256: str | None,
    after_sha256: str,
) -> str:
    canonical = json.dumps(
        {
            "path": path,
            "action": action,
            "before_sha256": before_sha256,
            "after_sha256": after_sha256,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(canonical)


class DeveloperActionTools:
    def __init__(
        self,
        workspace_root: str | os.PathLike[str],
        *,
        command_profiles: Iterable[CommandProfile] = (),
        command_executor: CommandExecutor = _subprocess_executor,
        max_file_bytes: int = _MAX_FILE_BYTES,
        max_diff_chars: int = _MAX_DIFF_CHARS,
    ) -> None:
        if max_file_bytes < 1024 or max_file_bytes > 2 * 1024 * 1024:
            raise ValueError("max_file_bytes must be between 1 KiB and 2 MiB")
        if max_diff_chars < 1024 or max_diff_chars > 256 * 1024:
            raise ValueError("max_diff_chars must be between 1 KiB and 256 KiB")
        if not callable(command_executor):
            raise ValueError("command_executor must be callable")
        self.workspace = WorkspaceReadTools(workspace_root, max_read_bytes=max_file_bytes)
        self.root = self.workspace.root
        self.max_file_bytes = max_file_bytes
        self.max_diff_chars = max_diff_chars
        self.command_executor = command_executor
        self.command_profiles: dict[str, CommandProfile] = {}
        for profile in command_profiles:
            if profile.command_id in self.command_profiles:
                raise ValueError(f"duplicate command profile: {profile.command_id}")
            cwd = self.workspace.resolve(profile.cwd)
            if not cwd.is_dir():
                raise ValueError(f"command profile cwd is not a directory: {profile.command_id}")
            self.command_profiles[profile.command_id] = profile

    def _target(self, raw: Any) -> tuple[Path, str]:
        value = str(raw or "").strip()
        if not value:
            raise ValueError("path is required")
        target = self.workspace.resolve(value, must_exist=False)
        relative = target.relative_to(self.root).as_posix()
        if target.exists():
            lexical = self.root / Path(value)
            if lexical.is_symlink():
                raise WorkspaceBoundaryError("workspace file change does not modify symlinks")
            if not target.is_file():
                raise ValueError("workspace file change target must be a file")
        parent = target.parent.resolve(strict=True)
        try:
            parent.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceBoundaryError("target parent escapes configured workspace") from exc
        if not parent.is_dir():
            raise ValueError("target parent must already exist")
        return target, relative

    def _read_current(self, target: Path) -> tuple[bytes, str]:
        if not target.exists():
            return b"", ""
        data = target.read_bytes()
        if len(data) > self.max_file_bytes:
            raise ValueError(f"existing file exceeds change limit: {len(data)} bytes")
        if b"\x00" in data:
            raise ValueError("binary files cannot be changed by the UTF-8 developer action tool")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("workspace file change requires UTF-8 text") from exc
        return data, text

    def _proposed_text(self, action: str, current: str, payload: Mapping[str, Any]) -> str:
        if action == "write":
            content = payload.get("content")
            if not isinstance(content, str):
                raise ValueError("write action requires string content")
            return content
        if action == "replace":
            find = payload.get("find")
            replacement = payload.get("replace")
            if not isinstance(find, str) or not find:
                raise ValueError("replace action requires non-empty find text")
            if not isinstance(replacement, str):
                raise ValueError("replace action requires string replace text")
            expected = int(payload.get("expected_occurrences", 1))
            if expected < 1 or expected > 100:
                raise ValueError("expected_occurrences must be between 1 and 100")
            actual = current.count(find)
            if actual != expected:
                raise ValueError(f"replace occurrence mismatch: expected {expected}, found {actual}")
            return current.replace(find, replacement, expected)
        raise ValueError(f"unsupported workspace.file.change action: {action}")

    def _preview(self, action: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        import difflib

        target, relative = self._target(payload.get("path"))
        before_exists = target.exists()
        before_bytes, current = self._read_current(target)
        proposed = self._proposed_text(action, current, payload)
        after_bytes = proposed.encode("utf-8")
        if len(after_bytes) > self.max_file_bytes:
            raise ValueError(f"proposed file exceeds change limit: {len(after_bytes)} bytes")
        diff = "".join(
            difflib.unified_diff(
                current.splitlines(keepends=True),
                proposed.splitlines(keepends=True),
                fromfile=f"a/{relative}",
                tofile=f"b/{relative}",
                n=3,
            )
        )
        diff_truncated = len(diff) > self.max_diff_chars
        if diff_truncated:
            diff = diff[: self.max_diff_chars - 3] + "..."
        before_sha = _sha256(before_bytes) if before_exists else None
        after_sha = _sha256(after_bytes)
        token = _change_token(
            path=relative,
            action=action,
            before_sha256=before_sha,
            after_sha256=after_sha,
        )
        return {
            "contract": DEVELOPER_ACTION_TOOLS_CONTRACT,
            "path": relative,
            "action": action,
            "exists_before": before_exists,
            "before_sha256": before_sha,
            "after_sha256": after_sha,
            "before_bytes": len(before_bytes),
            "after_bytes": len(after_bytes),
            "changed": before_bytes != after_bytes,
            "diff": diff,
            "diff_truncated": diff_truncated,
            "change_token": token,
            "approval_binding": "path+action+before_sha256+after_sha256",
            "rollback_contract": "fresh_reverse_preview_and_approval",
            "applied": False,
        }

    def file_change(self, action: str, payload: Mapping[str, Any], *, dry_run: bool) -> dict[str, Any]:
        preview = self._preview(action, payload)
        if dry_run:
            return preview
        supplied_token = str(payload.get("change_token") or "").strip()
        if not supplied_token:
            raise ValueError("approved apply requires change_token from a fresh dry-run preview")
        if supplied_token != preview["change_token"]:
            raise ValueError("change_token mismatch; workspace state or proposed change has drifted")
        if not preview["changed"]:
            return {
                **preview,
                "applied": True,
                "no_op": True,
                "verification": {"after_sha256": preview["after_sha256"], "matches": True},
            }
        target, _ = self._target(payload.get("path"))
        _, current = self._read_current(target)
        proposed = self._proposed_text(action, current, payload)
        data = proposed.encode("utf-8")
        previous_mode = target.stat().st_mode if target.exists() else None
        temp_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=str(target.parent),
                prefix=".research-os-change-",
                delete=False,
            ) as handle:
                temp_path = handle.name
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            if previous_mode is not None:
                os.chmod(temp_path, previous_mode)
            os.replace(temp_path, target)
            temp_path = None
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
        written = target.read_bytes()
        actual_sha = _sha256(written)
        if actual_sha != preview["after_sha256"]:
            raise RuntimeError("post-write verification hash mismatch")
        return {
            **preview,
            "applied": True,
            "no_op": False,
            "verification": {"after_sha256": actual_sha, "matches": True},
        }

    def command_run(self, payload: Mapping[str, Any], *, dry_run: bool) -> dict[str, Any]:
        command_id = str(payload.get("command_id") or "").strip()
        try:
            profile = self.command_profiles[command_id]
        except KeyError as exc:
            raise ValueError(f"unknown controlled command profile: {command_id}") from exc
        cwd = self.workspace.resolve(profile.cwd)
        relative_cwd = cwd.relative_to(self.root).as_posix()
        plan = {
            "contract": DEVELOPER_ACTION_TOOLS_CONTRACT,
            "command_id": profile.command_id,
            "category": profile.category,
            "argv": list(profile.argv),
            "cwd": relative_cwd if relative_cwd != "." else ".",
            "timeout_seconds": profile.timeout_seconds,
            "shell": False,
            "network_credentials_inherited": False,
            "dry_run": dry_run,
        }
        if dry_run:
            return {**plan, "executed": False}
        output = self.command_executor(profile, cwd, _safe_environment())
        if not isinstance(output, Mapping):
            raise TypeError("controlled command executor must return a mapping")
        return {**plan, "executed": True, "output": dict(output)}

    def adapter(self, tool_id: str):
        if tool_id == "workspace.file.change":
            def file_adapter(action: str, payload: Mapping[str, Any], dry_run: bool) -> Mapping[str, Any]:
                return self.file_change(action, payload, dry_run=dry_run)
            return file_adapter
        if tool_id == "workspace.command.run":
            def command_adapter(action: str, payload: Mapping[str, Any], dry_run: bool) -> Mapping[str, Any]:
                if action != "run":
                    raise ValueError(f"unsupported workspace.command.run action: {action}")
                return self.command_run(payload, dry_run=dry_run)
            return command_adapter
        raise ValueError(f"unsupported developer action tool: {tool_id}")

    def status(self) -> dict[str, Any]:
        return {
            "contract": DEVELOPER_ACTION_TOOLS_CONTRACT,
            "tool_count": len(DEVELOPER_ACTION_TOOL_DEFINITIONS),
            "workspace_root_exposed": False,
            "arbitrary_shell": False,
            "command_profiles": [
                {
                    "command_id": profile.command_id,
                    "category": profile.category,
                    "cwd": profile.cwd,
                    "timeout_seconds": profile.timeout_seconds,
                }
                for profile in sorted(self.command_profiles.values(), key=lambda item: item.command_id)
            ],
            "write_permission": ("workspace.read", "workspace.write"),
            "execute_permission": "workspace.execute",
            "real_mutations_require_controller_approval": True,
            "change_token_required": True,
            "network": False,
        }


def install_developer_action_tools(
    registry: ToolRegistry,
    workspace_root: str | os.PathLike[str],
    *,
    command_profiles: Iterable[CommandProfile] = (),
    command_executor: CommandExecutor = _subprocess_executor,
    max_file_bytes: int = _MAX_FILE_BYTES,
    max_diff_chars: int = _MAX_DIFF_CHARS,
) -> DeveloperActionTools:
    pack = DeveloperActionTools(
        workspace_root,
        command_profiles=command_profiles,
        command_executor=command_executor,
        max_file_bytes=max_file_bytes,
        max_diff_chars=max_diff_chars,
    )
    for definition in DEVELOPER_ACTION_TOOL_DEFINITIONS:
        try:
            existing = registry.get(definition.tool_id)
        except ValueError:
            registry.register(definition)
        else:
            if asdict(existing) != asdict(definition):
                raise ValueError(f"developer action tool definition collision: {definition.tool_id}")
        try:
            registry.register_adapter(definition.tool_id, pack.adapter(definition.tool_id))
        except ValueError as exc:
            if "already registered" not in str(exc):
                raise
            registry.register_adapter(definition.tool_id, pack.adapter(definition.tool_id), replace=True)
    return pack
