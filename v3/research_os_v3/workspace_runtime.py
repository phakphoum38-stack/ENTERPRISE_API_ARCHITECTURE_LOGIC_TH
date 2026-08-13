from __future__ import annotations

import hashlib
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path


class WorkspaceRuntime:
    """Read-only Full Control Center runtime confined to DRIVE_VIRTUAL_CLOUD."""

    MAX_LIST = 500
    MAX_TEXT_BYTES = 262_144

    def __init__(self, configured_root: Path | None = None) -> None:
        self.configured_root = configured_root

    def status(self) -> dict[str, object]:
        drive = self._detect_drive_root()
        repos = self.repositories()
        backups = self.backups()
        return {
            "drive_ready": drive is not None,
            "drive_root": str(drive) if drive is not None else None,
            "repository_count": len(repos),
            "backup_count": len(backups),
            "shell_mode": "research-os-commands",
            "arbitrary_os_shell": False,
        }

    def list_files(self, arguments: dict[str, object]) -> dict[str, object]:
        relative = str(arguments.get("path", "")).strip()
        root = self._required_drive_root()
        target = self._resolve_under(root, relative)
        if not target.exists():
            raise ValueError("Drive workspace path does not exist")
        if not target.is_dir():
            raise ValueError("Drive workspace path is not a directory")
        entries: list[dict[str, object]] = []
        for item in sorted(target.iterdir(), key=lambda value: (not value.is_dir(), value.name.lower()))[: self.MAX_LIST]:
            try:
                stat = item.stat()
            except OSError:
                continue
            entries.append(
                {
                    "name": item.name,
                    "path": item.relative_to(root).as_posix(),
                    "directory": item.is_dir(),
                    "size": stat.st_size if item.is_file() else 0,
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        return {
            "root": str(root),
            "path": target.relative_to(root).as_posix() if target != root else "",
            "entries": entries,
            "count": len(entries),
        }

    def read_text(self, arguments: dict[str, object]) -> dict[str, object]:
        relative = str(arguments.get("path", "")).strip()
        root = self._required_drive_root()
        target = self._resolve_under(root, relative)
        if not target.is_file():
            raise ValueError("Drive workspace file does not exist")
        size = target.stat().st_size
        if size > self.MAX_TEXT_BYTES:
            raise ValueError(f"text preview is limited to {self.MAX_TEXT_BYTES} bytes")
        raw = target.read_bytes()
        return {
            "path": target.relative_to(root).as_posix(),
            "size": size,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "text": raw.decode("utf-8", errors="replace"),
        }

    def repositories(self) -> list[dict[str, object]]:
        drive = self._detect_drive_root()
        if drive is None:
            return []
        base = drive / "github" / "repositories"
        if not base.is_dir():
            return []
        rows: list[dict[str, object]] = []
        for owner in sorted((item for item in base.iterdir() if item.is_dir()), key=lambda item: item.name.lower()):
            for repo in sorted((item for item in owner.iterdir() if item.is_dir()), key=lambda item: item.name.lower()):
                rows.append(
                    {
                        "owner": owner.name,
                        "name": repo.name,
                        "path": repo.relative_to(drive).as_posix(),
                        "files": self._count_files(repo, limit=20_000),
                        "bundle": self._bundle_info(drive, repo.name),
                    }
                )
                if len(rows) >= self.MAX_LIST:
                    return rows
        return rows

    def github_status(self) -> dict[str, object]:
        drive = self._detect_drive_root()
        repos = self.repositories()
        return {
            "mode": "local-mirror",
            "network_required_for_inventory": False,
            "drive_ready": drive is not None,
            "repositories": repos,
            "repository_count": len(repos),
            "note": "Online GitHub mutations require a separate governed integration/tool.",
        }

    def drive_status(self) -> dict[str, object]:
        drive = self._detect_drive_root()
        if drive is None:
            return {"configured": self.configured_root is not None or bool(os.environ.get("RESEARCH_OS_DRIVE_ROOT")), "available": False, "root": None, "directories": []}
        directories = [item.name for item in sorted(drive.iterdir(), key=lambda item: item.name.lower()) if item.is_dir()][:100]
        return {"configured": True, "available": True, "root": str(drive), "directories": directories}

    def runtime_status(self) -> dict[str, object]:
        return {
            "python": platform.python_version(),
            "executable": str(Path(sys.executable).resolve()),
            "platform": platform.platform(),
            "pid": os.getpid(),
            "service_process": True,
        }

    def installer_status(self) -> dict[str, object]:
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

    def backups(self) -> list[dict[str, object]]:
        drive = self._detect_drive_root()
        if drive is None:
            return []
        destination = drive / "backup" / "restore_points"
        if not destination.is_dir():
            return []
        rows: list[dict[str, object]] = []
        for item in sorted(destination.rglob("*.zip"), key=lambda path: path.stat().st_mtime, reverse=True)[: self.MAX_LIST]:
            try:
                stat = item.stat()
            except OSError:
                continue
            rows.append(
                {
                    "name": item.name,
                    "path": item.relative_to(drive).as_posix(),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "sha256": self._sha256_file(item),
                }
            )
        return rows

    def shell(self, arguments: dict[str, object]) -> dict[str, object]:
        command = str(arguments.get("command", "help")).strip().lower() or "help"
        if command == "help":
            return {"command": command, "commands": ["help", "workspace", "drive", "repos", "backups", "runtime", "installer"]}
        if command == "workspace":
            return {"command": command, "output": self.status()}
        if command == "drive":
            return {"command": command, "output": self.drive_status()}
        if command == "repos":
            return {"command": command, "output": self.repositories()}
        if command == "backups":
            return {"command": command, "output": self.backups()}
        if command == "runtime":
            return {"command": command, "output": self.runtime_status()}
        if command == "installer":
            return {"command": command, "output": self.installer_status()}
        raise ValueError("unknown Research OS shell command")

    def _required_drive_root(self) -> Path:
        root = self._detect_drive_root()
        if root is None:
            raise RuntimeError("DRIVE_VIRTUAL_CLOUD mirror is not configured or available")
        return root

    def _detect_drive_root(self) -> Path | None:
        candidates: list[Path] = []
        if self.configured_root is not None:
            candidates.append(self.configured_root)
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

    @staticmethod
    def _resolve_under(root: Path, relative: str) -> Path:
        if not relative or relative in {".", "/"}:
            return root.resolve()
        candidate_path = Path(relative.replace("\\", "/"))
        if candidate_path.is_absolute() or ".." in candidate_path.parts:
            raise ValueError("workspace paths must be relative and cannot contain '..'")
        target = (root / candidate_path).resolve()
        resolved_root = root.resolve()
        if target != resolved_root and resolved_root not in target.parents:
            raise ValueError("workspace path escaped Drive root")
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
