from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DriveToolPackage:
    name: str
    version: str
    runtime: str
    entrypoint: str
    sha256: str
    package_root: Path
    timeout_seconds: int = 15

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "version": self.version,
            "runtime": self.runtime,
            "entrypoint": self.entrypoint,
            "sha256": self.sha256,
            "timeout_seconds": self.timeout_seconds,
        }


class DriveToolRuntimeAdapter:
    """Execute owner-provided Drive tool packages from a locally synced mirror.

    Google Drive itself is storage, not a process host. This adapter consumes a
    local mirror root (for example the Drive for desktop G: mount), verifies a
    package manifest and entrypoint checksum, never invokes a shell, strips
    provider secrets from the child environment, and is intended to be called
    only through a V3 approval-gated tool definition.
    """

    MANIFEST = "tool.json"

    def __init__(self, root: Path | None = None) -> None:
        configured = root or (Path(os.environ["RESEARCH_OS_DRIVE_TOOL_ROOT"]) if os.environ.get("RESEARCH_OS_DRIVE_TOOL_ROOT") else None)
        self.root = configured.expanduser().resolve() if configured else None

    @property
    def available(self) -> bool:
        return bool(self.root and self.root.is_dir())

    def status(self) -> dict[str, object]:
        packages = self.discover() if self.available else []
        return {
            "configured": self.root is not None,
            "available": self.available,
            "root": str(self.root) if self.root else None,
            "package_count": len(packages),
            "execution": "local-mirror",
            "shell": False,
        }

    def discover(self) -> list[dict[str, object]]:
        if not self.available or self.root is None:
            return []
        packages: list[dict[str, object]] = []
        for manifest in sorted(self.root.glob(f"*/{self.MANIFEST}"))[:200]:
            try:
                package = self._load_manifest(manifest)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            packages.append(package.to_safe_dict())
        return packages

    def execute(self, arguments: dict[str, object]) -> dict[str, object]:
        if not self.available or self.root is None:
            raise RuntimeError("Drive tool runtime is not configured or local mirror is unavailable")
        name = str(arguments.get("name", "")).strip()
        if not name or any(part in name for part in ("/", "\\", "..")):
            raise ValueError("invalid Drive tool package name")
        package_root = (self.root / name).resolve()
        if package_root.parent != self.root:
            raise ValueError("Drive tool package escaped configured root")
        manifest = package_root / self.MANIFEST
        package = self._load_manifest(manifest)
        if package.name != name:
            raise ValueError("Drive tool manifest name does not match package directory")
        if package.runtime != "python":
            raise ValueError(f"unsupported Drive tool runtime: {package.runtime}")
        entrypoint = (package.package_root / package.entrypoint).resolve()
        if package.package_root not in entrypoint.parents:
            raise ValueError("Drive tool entrypoint escaped package root")
        if not entrypoint.is_file():
            raise RuntimeError("Drive tool entrypoint is missing")
        actual = hashlib.sha256(entrypoint.read_bytes()).hexdigest()
        if actual.lower() != package.sha256.lower():
            raise RuntimeError("Drive tool entrypoint checksum mismatch")
        raw_payload = arguments.get("arguments", {})
        if not isinstance(raw_payload, dict):
            raise ValueError("Drive tool arguments must be an object")

        env: dict[str, str] = {"PYTHONIOENCODING": "utf-8"}
        for key in ("PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE"):
            if os.environ.get(key):
                env[key] = os.environ[key]
        completed = subprocess.run(
            [sys.executable, str(entrypoint)],
            input=json.dumps(raw_payload, ensure_ascii=False),
            text=True,
            capture_output=True,
            cwd=str(package.package_root),
            env=env,
            timeout=package.timeout_seconds,
            check=False,
        )
        stdout = completed.stdout[-1_048_576:]
        stderr = completed.stderr[-1_048_576:]
        result: object
        try:
            result = json.loads(stdout) if stdout.strip() else None
        except json.JSONDecodeError:
            result = stdout
        return {
            "name": package.name,
            "version": package.version,
            "exit_code": completed.returncode,
            "result": result,
            "stderr": stderr,
            "checksum_verified": True,
        }

    def _load_manifest(self, manifest: Path) -> DriveToolPackage:
        if not manifest.is_file():
            raise RuntimeError("Drive tool manifest is missing")
        raw = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Drive tool manifest must be an object")
        package_root = manifest.parent.resolve()
        timeout = max(1, min(int(raw.get("timeout_seconds", 15)), 30))
        name = str(raw.get("name", "")).strip()
        version = str(raw.get("version", "")).strip()
        runtime = str(raw.get("runtime", "")).strip().lower()
        entrypoint = str(raw.get("entrypoint", "")).strip()
        sha256 = str(raw.get("sha256", "")).strip().lower()
        if not name or not version or not runtime or not entrypoint or len(sha256) != 64:
            raise ValueError("Drive tool manifest is incomplete")
        return DriveToolPackage(name, version, runtime, entrypoint, sha256, package_root, timeout)
