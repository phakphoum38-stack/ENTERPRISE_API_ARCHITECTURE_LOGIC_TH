"""Verified local installer/bootstrap primitives for the Research OS Universal Runner."""
from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class InstallationError(ValueError):
    """Raised when a package cannot be safely verified or installed."""


@dataclass(frozen=True)
class PackageManifest:
    package_id: str
    version: str
    platform: str
    architecture: str
    source_sha: str
    artifact_sha256: str
    files: Mapping[str, str]

    @classmethod
    def from_path(cls, path: Path) -> "PackageManifest":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise InstallationError(f"invalid package manifest: {path}") from exc
        required = ("package_id", "version", "platform", "architecture", "source_sha", "artifact_sha256", "files")
        missing = [key for key in required if not data.get(key)]
        if missing:
            raise InstallationError(f"manifest missing required fields: {', '.join(missing)}")
        files = data["files"]
        if not isinstance(files, dict) or not files:
            raise InstallationError("manifest files must be a non-empty object")
        return cls(
            str(data["package_id"]), str(data["version"]), str(data["platform"]),
            str(data["architecture"]), str(data["source_sha"]),
            str(data["artifact_sha256"]), {str(k): str(v) for k, v in files.items()},
        )


def sha256_file(path: Path) -> str:
    if not path.is_file():
        raise InstallationError(f"artifact is not a file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_relative_path(raw: str) -> Path:
    candidate = Path(raw)
    if candidate.is_absolute() or ".." in candidate.parts or not raw.strip():
        raise InstallationError(f"unsafe package path: {raw}")
    return candidate


def verify_package(package_root: Path, manifest: PackageManifest) -> None:
    if not package_root.is_dir():
        raise InstallationError(f"package root is missing: {package_root}")
    for relative, expected_digest in manifest.files.items():
        safe = _safe_relative_path(relative)
        actual = sha256_file(package_root / safe)
        if actual.lower() != expected_digest.lower():
            raise InstallationError(
                f"package digest mismatch for {relative}: expected {expected_digest}, actual {actual}"
            )


def verify_manifest(package_root: Path, manifest_path: Path) -> PackageManifest:
    manifest = PackageManifest.from_path(manifest_path)
    if manifest_path.parent.resolve() != package_root.resolve():
        raise InstallationError("manifest must be located at package root")
    verify_package(package_root, manifest)
    return manifest


def install_verified_package(package_root: Path, manifest_path: Path, target_root: Path) -> PackageManifest:
    """Install only a verified package using disposable staging."""
    manifest = verify_manifest(package_root, manifest_path)
    target_root = target_root.resolve()
    target_root.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{target_root.name}.stage-", dir=target_root.parent))
    try:
        for relative in manifest.files:
            safe = _safe_relative_path(relative)
            destination = stage / safe
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(package_root / safe, destination)
        marker = stage / "INSTALLATION_MANIFEST.json"
        marker.write_text(json.dumps({
            "package_id": manifest.package_id,
            "version": manifest.version,
            "platform": manifest.platform,
            "architecture": manifest.architecture,
            "source_sha": manifest.source_sha,
            "artifact_sha256": manifest.artifact_sha256,
            "installer_mode": "VERIFIED_LOCAL_COPY"
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if target_root.exists():
            backup = target_root.with_name(target_root.name + ".previous")
            if backup.exists():
                shutil.rmtree(backup)
            target_root.replace(backup)
            stage.replace(target_root)
            shutil.rmtree(backup)
        else:
            stage.replace(target_root)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return manifest


def build_bootstrap_plan(*, source: Path, platform_name: str, architecture: str) -> tuple[str, ...]:
    if not source.exists():
        raise InstallationError(f"bootstrap source is missing: {source}")
    if not platform_name.strip() or not architecture.strip():
        raise InstallationError("platform and architecture are required")
    return ("DISCOVER", "DOWNLOAD", "VERIFY", "STAGE", "INSTALL",
            "REGISTER", "DISCOVER_CAPABILITIES", "HEALTH_CHECK", "READY")


__all__ = ["InstallationError", "PackageManifest", "build_bootstrap_plan",
           "install_verified_package", "sha256_file", "verify_manifest", "verify_package"]