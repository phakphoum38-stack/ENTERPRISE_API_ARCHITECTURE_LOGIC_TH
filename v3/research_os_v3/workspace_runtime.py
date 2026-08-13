from __future__ import annotations

import hashlib
import os
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .storage import DataLayout
from .user_context import UserContext


@dataclass(frozen=True)
class WorkspaceRoot:
    name: str
    path: Path
    kind: str

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "path": str(self.path), "kind": self.kind}


class WorkspaceRuntime:
    """Read-only Full Control Center runtime with strict root confinement."""

    MAX_LIST = 500
    MAX_TEXT_BYTES = 262_144

    def __init__(self, data_layout: DataLayout) -> None:
        self.data_layout = data_layout

    def roots(self, context: UserContext) -> tuple[WorkspaceRoot, ...]:
        user_root = self.data_layout.for_user(context).ensure().root.resolve()
        roots = [WorkspaceRoot("user", user_root, "user-data")]
        drive = self._detect_drive_root()
        if drive is not None:
            roots.append(WorkspaceRoot("drive", drive, "google-drive-mirror"))
        return tuple(roots)

    def status(self, context: UserContext) -> dict[str, object]:
        roots = self.roots(context)
        drive = next((item for item in roots if item.name == "drive"), None)
        repos = self.repositories(context)
        backups = self.backups(context)
        return {
            "roots": [item.to_dict() for item in roots],
            "drive_ready": drive is not None,
            "repository_count": len(repos),
            "backup_count": len(backups),
            "shell_mode": "research-os-commands",
            "arbitrary_os_shell": False,
        }

    def list_files(self, context: UserContext, arguments: dict[str, object]) -> dict[str, object]:
        root_name = str(arguments.get("root", "user")).strip().lower() or "user"
        relative = str(arguments.get("path", "")).strip()
        root = self._root(context, root_name)
        target = self._resolve_under(root.path, relative)
        if not target.exists():
            raise ValueError("workspace path does not exist")
        if not target.is_dir():
            raise ValueError("workspace path is not a directory")
        entries: list[dict[str, object]] = []
        for item in sorted(target.iterdir(), key=lambda value: (not value.is_dir(), value.name.lower()))[: self.MAX_LIST]:
            try:
                stat = item.stat()
            except OSError:
                continue
            entries.append(
                {
                    "name": item.name,
                    "path": item.relative_to(root.path).as_posix(),
                    "directory": item.is_dir(),
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        return {
            "root": root.to_dict(),
            "path": target.relative_to(root.path).as_posix() if target != root.path else "",
            "entries": entries,
            "count": len(entries),
        }

    def read_text(self, context: UserContext, arguments: dict[str, object]) -> dict[str, object]:
        root_name = str(arguments.get("root", "user")).strip().lower() or "user"
        relative = str(arguments.get("path", "")).strip()
        root = self._root(context, root_name)
        target = self._resolve_under(root.path, relative)
        if not target.is_file():
            raise ValueError("workspace file does not exist")
        size = target.stat().st_size
        if size > self.MAX_TEXT_BYTES:
            raise ValueError(f"text preview is limited to {self.MAX_TEXT_BYTES} bytes")
        raw = target.read_bytes()
        return {
            "root": root.name,
            "path": target.relative_to(root.path).as_posix(),
            "size": size,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "text": raw.decode("utf-8", errors="replace"),
        }

    def repositories(self, context: UserContext) -> list[dict[str, object]]:
        drive = self._optional_root(context, "drive")
        if drive is None:
            return []
        base = drive.path / "github" / "repositories"
        if not base.is_dir():
            return []
        rows: list[dict[str, object]] = []
        for owner in sorted((item for item in base.iterdir() if item.is_dir()), key=lambda item: item.name.lower()):
            for repo in sorted((item for item in owner.iterdir() if item.is_dir()), key=lambda item: item.name.lower()):
                rows.append(
                    {
                        "owner": owner.name,
                        "name": repo.name,
                        "path": repo.relative_to(drive.path).as_posix(),
                        "files": self._count_files(repo, limit=20_000),
                        "bundle": self._bundle_info(drive.path, repo.name),
                    }
                )
                if len(rows) >= self.MAX_LIST:
                    return rows
        return rows

    def github_status(self, context: UserContext) -> dict[str, object]:
        drive = self._optional_root(context, "drive")
        repos = self.repositories(context)
        return {
            "mode": "local-mirror",
            "network_required_for_inventory": False,
            "drive_ready": drive is not None,
            "repositories": repos,
            "repository_count": len(repos),
            "note": "Online GitHub mutations require a separate governed integration/tool.",
        }

    def drive_status(self, context: UserContext) -> dict[str, object]:
        drive = self._optional_root(context, "drive")
        if drive is None:
            return {"configured": False, "available": False, "root": None, "directories": []}
        directories = [item.name for item in sorted(drive.path.iterdir(), key=lambda item: item.name.lower()) if item.is_dir()][:100]
        return {"configured": True, "available": True, "root": str(drive.path), "directories": directories}

    def runtime_status(self, context: UserContext) -> dict[str, object]:
        user = self.data_layout.for_user(context).ensure()
        return {
            "python": platform.python_version(),
            "executable": str(Path(sys.executable).resolve()),
            "platform": platform.platform(),
            "user_data_root": str(user.root.resolve()),
            "pid": os.getpid(),
            "service_process": True,
        }

    def installer_status(self, context: UserContext) -> dict[str, object]:
        executable = Path(sys.executable).resolve()
        candidates = [
            executable.parent,
            executable.parent.parent,
            Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Research OS V3",
        ]
        install_root = next((item for item in candidates if item.exists() and "Research" in str(item)), None)
        build_sha = None
        if install_root is not None:
            for candidate in (install_root / "BUILD_SHA.txt", install_root.parent / "BUILD_SHA.txt"):
                if candidate.is_file():
                    build_sha = candidate.read_text(encoding="utf-8", errors="replace").strip()
                    break
        return {
            "installed": install_root is not None,
            "install_root": str(install_root) if install_root is not None else None,
            "build_sha": build_sha,
            "upgrade_policy": "in-place-preserve-data",
            "uninstall_policy": "remove-app-and-service-preserve-data",
        }

    def backups(self, context: UserContext) -> list[dict[str, object]]:
        destination = self._backup_root(context)
        if not destination.is_dir():
            return []
        rows: list[dict[str, object]] = []
        for item in sorted(destination.glob("*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)[: self.MAX_LIST]:
            stat = item.stat()
            rows.append(
                {
                    "name": item.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "sha256": self._sha256_file(item),
                }
            )
        return rows

    def shell(self, context: UserContext, arguments: dict[str, object]) -> dict[str, object]:
        command = str(arguments.get("command", "help")).strip().lower() or "help"
        if command == "help":
            return {"command": command, "commands": ["help", "workspace", "drive", "repos", "backups", "runtime", "installer"]}
        if command == "workspace":
            return {"command": command, "output": self.status(context)}
        if command == "drive":
            return {"command": command, "output": self.drive_status(context)}
        if command == "repos":
            return {"command": command, "output": self.repositories(context)}
        if command == "backups":
            return {"command": command, "output": self.backups(context)}
        if command == "runtime":
            return {"command": command, "output": self.runtime_status(context)}
        if command == "installer":
            return {"command": command, "output": self.installer_status(context)}
        raise ValueError("unknown Research OS shell command")

    def _root(self, context: UserContext, name: str) -> WorkspaceRoot:
        root = self._optional_root(context, name)
        if root is None:
            raise RuntimeError(f"workspace root is unavailable: {name}")
        return root

    def _optional_root(self, context: UserContext, name: str) -> WorkspaceRoot | None:
        return next((item for item in self.roots(context) if item.name == name), None)

    def _detect_drive_root(self) -> Path | None:
        candidates: list[Path] = []
        configured = os.environ.get("RESEARCH_OS_DRIVE_ROOT")
        if configured:
            candidates.append(Path(configured).expanduser())
        tool_root = os.environ.get("RESEARCH_OS_DRIVE_TOOL_ROOT")
        if tool_root:
            current = Path(tool_root).expanduser()
            candidates.append(current)
            candidates.extend(current.parents)
        if os.name == "nt":
            candidates.extend(
                [
                    Path(r"G:\ไดรฟ์ของฉัน\DRIVE_VIRTUAL_CLOUD"),
                    Path(r"G:\My Drive\DRIVE_VIRTUAL_CLOUD"),
                    Path(r"G:\DRIVE_VIRTUAL_CLOUD"),
                ]
            )
        seen: set[str] = set()
        for candidate in candidates:
            try:
                resolved = candidate.resolve()
            except OSError:
                continue
            key = str(resolved).lower()
            if key in seen:
                continue
            seen.add(key)
            if resolved.is_dir() and (resolved.name == "DRIVE_VIRTUAL_CLOUD" or (resolved / "github").is_dir()):
                return resolved
        return None

    def _backup_root(self, context: UserContext) -> Path:
        drive = self._optional_root(context, "drive")
        if drive is not None:
            return (drive.path / "backup" / "restore_points" / context.user_id / context.profile_id).resolve()
        return (self.data_layout.for_user(context).ensure().root / "backups").resolve()

    def _resolve_under(self, root: Path, relative: str) -> Path:
        if not relative or relative in {".", "/"}:
            return root.resolve()
        candidate_path = Path(relative.replace("\\", "/"))
        if candidate_path.is_absolute() or ".." in candidate_path.parts:
            raise ValueError("workspace paths must be relative and cannot contain '..'")
        target = (root / candidate_path).resolve()
        resolved_root = root.resolve()
        if target != resolved_root and resolved_root not in target.parents:
            raise ValueError("workspace path escaped allowed root")
        return target

    def _bundle_info(self, drive_root: Path, repo_name: str) -> dict[str, object] | None:
        bundle = (drive_root / "github" / "bundles" / "full" / f"{repo_name}.bundle").resolve()
        if not bundle.is_file():
            return None
        return {"name": bundle.name, "size": bundle.stat().st_size, "sha256": self._sha256_file(bundle)}

    @staticmethod
    def _count_files(root: Path, *, limit: int) -> int:
        count = 0
        try:
            for item in root.rglob("*"):
                if item.is_file():
                    count += 1
                    if count >= limit:
                        break
        except OSError:
            pass
        return count

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()
