#!/usr/bin/env python3
"""Sandboxed read-only workspace tools for Research OS AI Brain.

Phase 5 introduces the first real workspace adapters. They are deliberately
read-only, require an explicitly supplied workspace root, never execute shell
commands, keep all returned paths relative to that root, and reject traversal,
secret files, binary files and oversized reads.
"""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import Any

from v2_tool_registry import ToolDefinition, ToolRegistry


WORKSPACE_READ_TOOLS_CONTRACT = "brain-workspace-read-tools-phase-5"

_IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".dart_tool",
    ".gradle",
    ".venv",
    "venv",
    "node_modules",
    "build",
    "dist",
    "coverage",
    "__pycache__",
}

_SECRET_DIRS = {".ssh", ".aws", ".azure", ".kube", ".gnupg"}
_SECRET_FILENAMES = {
    "credentials.json",
    "client_secret.json",
    "secrets.json",
    "service-account.json",
    "service_account.json",
    "id_rsa",
    "id_ed25519",
}
_SECRET_SUFFIXES = {".key", ".p12", ".pfx"}
_TEXT_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".css",
    ".dart",
    ".go",
    ".gradle",
    ".graphql",
    ".h",
    ".hpp",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".kts",
    ".md",
    ".php",
    ".properties",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".sql",
    ".swift",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".yaml",
    ".yml",
}
_TEXT_NAMES = {
    "Dockerfile",
    "Makefile",
    "CMakeLists.txt",
    "Podfile",
    "Gemfile",
}


WORKSPACE_READ_TOOL_DEFINITIONS: tuple[ToolDefinition, ...] = (
    ToolDefinition(
        "workspace.file.read",
        "1.0.0",
        "Workspace File Read",
        "Reads a bounded UTF-8 text file inside the configured workspace sandbox.",
        ("workspace_file_read", "source_inspection", "file_read"),
        permissions=("workspace.read",),
        mutating=False,
        network=False,
        secret_access=False,
        idempotent=True,
        supports_dry_run=True,
    ),
    ToolDefinition(
        "workspace.directory.list",
        "1.0.0",
        "Workspace Directory List",
        "Lists one directory inside the workspace sandbox without following it outside the root.",
        ("workspace_browse", "directory_list"),
        permissions=("workspace.read",),
        mutating=False,
        network=False,
        secret_access=False,
        idempotent=True,
        supports_dry_run=True,
    ),
    ToolDefinition(
        "workspace.code.search",
        "1.0.0",
        "Workspace Code Search",
        "Performs bounded case-insensitive text search across safe source files in the workspace.",
        ("code_search", "repository_search", "source_inspection"),
        permissions=("workspace.read",),
        mutating=False,
        network=False,
        secret_access=False,
        idempotent=True,
        supports_dry_run=True,
    ),
    ToolDefinition(
        "workspace.repository.map",
        "1.0.0",
        "Workspace Repository Map",
        "Builds a bounded relative-path repository map for architecture discovery.",
        ("repository_map", "architecture_discovery", "workspace_browse"),
        permissions=("workspace.read",),
        mutating=False,
        network=False,
        secret_access=False,
        idempotent=True,
        supports_dry_run=True,
    ),
    ToolDefinition(
        "workspace.build.inspect",
        "1.0.0",
        "Workspace Build Test Inspector",
        "Detects build manifests, CI workflows and test files without executing commands.",
        ("build_inspection", "test_inspection", "ci_config_inspection"),
        permissions=("workspace.read",),
        mutating=False,
        network=False,
        secret_access=False,
        idempotent=True,
        supports_dry_run=True,
    ),
)


class WorkspaceBoundaryError(ValueError):
    pass


class WorkspaceReadTools:
    def __init__(
        self,
        workspace_root: str | os.PathLike[str],
        *,
        max_read_bytes: int = 256 * 1024,
        max_search_results: int = 200,
        max_map_entries: int = 2000,
        max_scan_files: int = 5000,
    ) -> None:
        root = Path(workspace_root).expanduser().resolve(strict=True)
        if not root.is_dir():
            raise ValueError("workspace_root must be a directory")
        if max_read_bytes < 1024 or max_read_bytes > 2 * 1024 * 1024:
            raise ValueError("max_read_bytes must be between 1 KiB and 2 MiB")
        if max_search_results < 1 or max_search_results > 1000:
            raise ValueError("max_search_results must be between 1 and 1000")
        if max_map_entries < 1 or max_map_entries > 10000:
            raise ValueError("max_map_entries must be between 1 and 10000")
        if max_scan_files < 1 or max_scan_files > 50000:
            raise ValueError("max_scan_files must be between 1 and 50000")
        self.root = root
        self.max_read_bytes = max_read_bytes
        self.max_search_results = max_search_results
        self.max_map_entries = max_map_entries
        self.max_scan_files = max_scan_files

    @staticmethod
    def _is_secret_path(relative: Path) -> bool:
        parts = tuple(part.casefold() for part in relative.parts)
        if any(part in _SECRET_DIRS for part in parts):
            return True
        name = relative.name
        folded = name.casefold()
        if folded.startswith(".env") and folded != ".env.example":
            return True
        if folded in _SECRET_FILENAMES:
            return True
        if Path(folded).suffix in _SECRET_SUFFIXES:
            return True
        return False

    @staticmethod
    def _is_ignored_dir(name: str) -> bool:
        folded = name.casefold()
        return folded in {item.casefold() for item in _IGNORED_DIRS | _SECRET_DIRS}

    def _relative(self, path: Path) -> Path:
        try:
            return path.relative_to(self.root)
        except ValueError as exc:
            raise WorkspaceBoundaryError("path escapes configured workspace") from exc

    def resolve(self, requested: str | os.PathLike[str] | None, *, must_exist: bool = True) -> Path:
        raw = str(requested or ".").strip() or "."
        candidate = Path(raw)
        if candidate.is_absolute():
            raise WorkspaceBoundaryError("absolute paths are not allowed")
        lexical = Path(os.path.normpath(raw))
        if lexical == Path("..") or ".." in lexical.parts:
            raise WorkspaceBoundaryError("parent traversal is not allowed")
        target = (self.root / lexical).resolve(strict=must_exist)
        relative = self._relative(target)
        if self._is_secret_path(relative):
            raise WorkspaceBoundaryError("secret-bearing workspace path is blocked")
        return target

    def _safe_relative_string(self, path: Path) -> str:
        relative = self._relative(path.resolve(strict=True))
        if self._is_secret_path(relative):
            raise WorkspaceBoundaryError("secret-bearing workspace path is blocked")
        text = relative.as_posix()
        return "." if text == "." else text

    @staticmethod
    def _looks_text(path: Path) -> bool:
        return path.name in _TEXT_NAMES or path.suffix.casefold() in _TEXT_SUFFIXES

    def _read_text(self, path: Path) -> str:
        if not path.is_file():
            raise ValueError("requested path is not a file")
        size = path.stat().st_size
        if size > self.max_read_bytes:
            raise ValueError(f"file exceeds read limit: {size} bytes")
        data = path.read_bytes()
        if b"\x00" in data:
            raise ValueError("binary files are not readable by workspace text tools")
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("workspace text tools require UTF-8 files") from exc

    def read_file(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        path = self.resolve(str(payload.get("path") or ""))
        content = self._read_text(path)
        line_count = content.count("\n") + (1 if content else 0)
        return {
            "contract": WORKSPACE_READ_TOOLS_CONTRACT,
            "path": self._safe_relative_string(path),
            "content": content,
            "bytes": len(content.encode("utf-8")),
            "line_count": line_count,
            "read_only": True,
        }

    def list_directory(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        path = self.resolve(str(payload.get("path") or "."))
        if not path.is_dir():
            raise ValueError("requested path is not a directory")
        limit = int(payload.get("limit") or 200)
        limit = min(max(limit, 1), 1000)
        entries: list[dict[str, Any]] = []
        skipped_sensitive = 0
        for child in sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.casefold())):
            if len(entries) >= limit:
                break
            relative = self._relative(child.resolve(strict=True))
            if self._is_secret_path(relative):
                skipped_sensitive += 1
                continue
            if child.is_dir() and self._is_ignored_dir(child.name):
                continue
            item: dict[str, Any] = {
                "name": child.name,
                "path": relative.as_posix(),
                "type": "directory" if child.is_dir() else "file",
            }
            if child.is_file():
                item["bytes"] = child.stat().st_size
            entries.append(item)
        return {
            "contract": WORKSPACE_READ_TOOLS_CONTRACT,
            "path": self._safe_relative_string(path),
            "entries": entries,
            "count": len(entries),
            "skipped_sensitive": skipped_sensitive,
            "truncated": len(entries) >= limit,
            "read_only": True,
        }

    def _iter_safe_files(self, start: Path):
        scanned = 0
        if start.is_file():
            candidates = [start]
        else:
            candidates = None
        if candidates is not None:
            for path in candidates:
                relative = self._relative(path.resolve(strict=True))
                if not self._is_secret_path(relative):
                    yield path
            return

        for current, dirs, files in os.walk(start, followlinks=False):
            current_path = Path(current)
            safe_dirs: list[str] = []
            for directory in sorted(dirs):
                if self._is_ignored_dir(directory):
                    continue
                candidate = (current_path / directory).resolve(strict=True)
                try:
                    relative = self._relative(candidate)
                except WorkspaceBoundaryError:
                    continue
                if self._is_secret_path(relative):
                    continue
                safe_dirs.append(directory)
            dirs[:] = safe_dirs

            for name in sorted(files):
                if scanned >= self.max_scan_files:
                    return
                path = current_path / name
                try:
                    resolved = path.resolve(strict=True)
                    relative = self._relative(resolved)
                except (OSError, WorkspaceBoundaryError):
                    continue
                if self._is_secret_path(relative):
                    continue
                scanned += 1
                yield resolved

    def search_code(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        query = str(payload.get("query") or "").strip()
        if len(query) < 2:
            raise ValueError("search query must contain at least two characters")
        start = self.resolve(str(payload.get("path") or "."))
        limit = int(payload.get("limit") or self.max_search_results)
        limit = min(max(limit, 1), self.max_search_results)
        raw_glob = str(payload.get("glob") or "").strip()
        folded_query = query.casefold()
        matches: list[dict[str, Any]] = []
        files_examined = 0

        for path in self._iter_safe_files(start):
            if len(matches) >= limit:
                break
            relative = self._relative(path)
            if raw_glob and not fnmatch.fnmatch(relative.as_posix(), raw_glob):
                continue
            if not self._looks_text(path):
                continue
            if path.stat().st_size > self.max_read_bytes:
                continue
            try:
                content = self._read_text(path)
            except (OSError, ValueError):
                continue
            files_examined += 1
            for line_number, line in enumerate(content.splitlines(), start=1):
                index = line.casefold().find(folded_query)
                if index < 0:
                    continue
                preview = line.strip()
                if len(preview) > 240:
                    preview = preview[:237] + "..."
                matches.append(
                    {
                        "path": relative.as_posix(),
                        "line": line_number,
                        "column": index + 1,
                        "preview": preview,
                    }
                )
                if len(matches) >= limit:
                    break

        return {
            "contract": WORKSPACE_READ_TOOLS_CONTRACT,
            "query": query,
            "path": self._safe_relative_string(start),
            "matches": matches,
            "count": len(matches),
            "files_examined": files_examined,
            "truncated": len(matches) >= limit,
            "read_only": True,
        }

    def repository_map(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        start = self.resolve(str(payload.get("path") or "."))
        if not start.is_dir():
            raise ValueError("repository map path must be a directory")
        max_depth = int(payload.get("max_depth") or 4)
        max_depth = min(max(max_depth, 0), 8)
        limit = int(payload.get("limit") or self.max_map_entries)
        limit = min(max(limit, 1), self.max_map_entries)
        start_relative = self._relative(start)
        entries: list[dict[str, Any]] = []

        for current, dirs, files in os.walk(start, followlinks=False):
            current_path = Path(current)
            current_relative = self._relative(current_path.resolve(strict=True))
            depth = len(current_relative.parts) - len(start_relative.parts)
            if depth >= max_depth:
                dirs[:] = []
            else:
                dirs[:] = [
                    name
                    for name in sorted(dirs)
                    if not self._is_ignored_dir(name)
                    and not self._is_secret_path(self._relative((current_path / name).resolve(strict=True)))
                ]

            for name in sorted(dirs):
                if len(entries) >= limit:
                    break
                path = (current_path / name).resolve(strict=True)
                entries.append({"path": self._relative(path).as_posix(), "type": "directory"})
            if len(entries) >= limit:
                break

            for name in sorted(files):
                if len(entries) >= limit:
                    break
                path = current_path / name
                try:
                    resolved = path.resolve(strict=True)
                    relative = self._relative(resolved)
                except (OSError, WorkspaceBoundaryError):
                    continue
                if self._is_secret_path(relative):
                    continue
                entries.append(
                    {
                        "path": relative.as_posix(),
                        "type": "file",
                        "bytes": resolved.stat().st_size,
                    }
                )
            if len(entries) >= limit:
                break

        return {
            "contract": WORKSPACE_READ_TOOLS_CONTRACT,
            "path": self._safe_relative_string(start),
            "entries": entries,
            "count": len(entries),
            "max_depth": max_depth,
            "truncated": len(entries) >= limit,
            "read_only": True,
        }

    def inspect_build(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        start = self.resolve(str(payload.get("path") or "."))
        if not start.is_dir():
            raise ValueError("build inspection path must be a directory")

        manifest_names = {
            "pubspec.yaml",
            "package.json",
            "pyproject.toml",
            "requirements.txt",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "build.gradle.kts",
            "CMakeLists.txt",
            "Dockerfile",
        }
        manifests: list[str] = []
        workflows: list[str] = []
        installers: list[str] = []
        tests: list[str] = []
        files_examined = 0

        for path in self._iter_safe_files(start):
            if files_examined >= self.max_scan_files:
                break
            files_examined += 1
            relative = self._relative(path).as_posix()
            name = path.name
            folded = relative.casefold()
            if name in manifest_names:
                manifests.append(relative)
            if folded.startswith(".github/workflows/") and path.suffix.casefold() in {".yml", ".yaml"}:
                workflows.append(relative)
            if folded.startswith("installer/") and path.suffix.casefold() in {".iss", ".wxs", ".nsi"}:
                installers.append(relative)
            lowered_name = name.casefold()
            if (
                lowered_name.startswith("test_")
                or lowered_name.endswith("_test.py")
                or lowered_name.endswith("_test.dart")
                or "/test/" in f"/{folded}"
                or "/tests/" in f"/{folded}"
            ):
                tests.append(relative)

        return {
            "contract": WORKSPACE_READ_TOOLS_CONTRACT,
            "path": self._safe_relative_string(start),
            "manifests": sorted(dict.fromkeys(manifests)),
            "workflows": sorted(dict.fromkeys(workflows)),
            "installers": sorted(dict.fromkeys(installers)),
            "tests": sorted(dict.fromkeys(tests)),
            "summary": {
                "manifest_count": len(set(manifests)),
                "workflow_count": len(set(workflows)),
                "installer_count": len(set(installers)),
                "test_file_count": len(set(tests)),
                "files_examined": files_examined,
            },
            "commands_executed": 0,
            "read_only": True,
        }

    def adapter(self, tool_id: str):
        handlers = {
            "workspace.file.read": ("read", self.read_file),
            "workspace.directory.list": ("list", self.list_directory),
            "workspace.code.search": ("search", self.search_code),
            "workspace.repository.map": ("map", self.repository_map),
            "workspace.build.inspect": ("inspect", self.inspect_build),
        }
        try:
            expected_action, handler = handlers[tool_id]
        except KeyError as exc:
            raise ValueError(f"unsupported workspace tool: {tool_id}") from exc

        def invoke(action: str, payload: Mapping[str, Any], dry_run: bool) -> Mapping[str, Any]:
            del dry_run
            if action != expected_action:
                raise ValueError(f"unsupported {tool_id} action: {action}")
            return handler(payload)

        return invoke

    def status(self) -> dict[str, Any]:
        return {
            "contract": WORKSPACE_READ_TOOLS_CONTRACT,
            "configured": True,
            "workspace_name": self.root.name,
            "tool_count": len(WORKSPACE_READ_TOOL_DEFINITIONS),
            "read_only": True,
            "shell_execution": False,
            "network": False,
            "absolute_paths_returned": False,
            "secret_paths_blocked": True,
            "max_read_bytes": self.max_read_bytes,
            "max_search_results": self.max_search_results,
            "max_map_entries": self.max_map_entries,
            "max_scan_files": self.max_scan_files,
        }


def install_workspace_read_tools(
    registry: ToolRegistry,
    workspace_root: str | os.PathLike[str],
    **limits: Any,
) -> WorkspaceReadTools:
    """Register Phase 5 workspace ToolDefinitions and bind real read-only adapters.

    Re-installation is allowed only when an existing definition is exactly the
    same contract; foreign/colliding definitions are rejected instead of being
    silently replaced.
    """

    pack = WorkspaceReadTools(workspace_root, **limits)
    for definition in WORKSPACE_READ_TOOL_DEFINITIONS:
        try:
            existing = registry.get(definition.tool_id)
        except ValueError:
            registry.register(definition)
        else:
            if asdict(existing) != asdict(definition):
                raise ValueError(f"workspace tool definition collision: {definition.tool_id}")
        try:
            registry.register_adapter(definition.tool_id, pack.adapter(definition.tool_id))
        except ValueError as exc:
            if "already registered" not in str(exc):
                raise
            registry.register_adapter(
                definition.tool_id,
                pack.adapter(definition.tool_id),
                replace=True,
            )
    return pack
