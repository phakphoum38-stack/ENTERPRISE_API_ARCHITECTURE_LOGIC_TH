#!/usr/bin/env python3
"""Build and validate the standalone Research OS file-owner package."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterable


OWNER_PACKAGE_CONTRACT = "research-os-file-owner-package-v1"
OWNER_PACKAGE_FILES = (
    "tools/research_os_api/v2_file_ownership_boundary.py",
)
_FORBIDDEN_PATH_TOKENS = (
    "cyber",
    "web_security",
    "website",
    "browser",
    "oauth",
)
_FORBIDDEN_CONTENT_TOKENS = (
    "cyber",
    "web security",
    "website",
    "browser security",
    "oauth",
    "http://",
    "https://",
    "เว็บไซต์",
    "ไซเบอร์",
)


class OwnerPackageError(RuntimeError):
    pass


def manifest() -> dict[str, Any]:
    return {
        "contract": OWNER_PACKAGE_CONTRACT,
        "package": "file-owner",
        "files": list(OWNER_PACKAGE_FILES),
        "exact_allowlist": True,
        "external_service_files_included": False,
        "network_features_included": False,
        "owner_mutation_backend_included": False,
    }


def validate_paths(paths: Iterable[str]) -> list[str]:
    normalized = [str(Path(path).as_posix()).lstrip("./") for path in paths]
    unexpected = sorted(set(normalized) - set(OWNER_PACKAGE_FILES))
    missing = sorted(set(OWNER_PACKAGE_FILES) - set(normalized))
    if unexpected:
        raise OwnerPackageError(f"unexpected owner-package files: {unexpected}")
    if missing:
        raise OwnerPackageError(f"missing owner-package files: {missing}")
    for path in normalized:
        lowered = path.casefold()
        if any(token in lowered for token in _FORBIDDEN_PATH_TOKENS):
            raise OwnerPackageError(f"forbidden owner-package path: {path}")
    return normalized


def validate_source_tree(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_paths(OWNER_PACKAGE_FILES)
    checked: list[str] = []
    for relative in OWNER_PACKAGE_FILES:
        source = (root / relative).resolve()
        if not source.is_file() or root not in source.parents:
            raise OwnerPackageError(f"owner-package source missing or outside repository: {relative}")
        text = source.read_text(encoding="utf-8")
        lowered = text.casefold()
        hits = [token for token in _FORBIDDEN_CONTENT_TOKENS if token.casefold() in lowered]
        if hits:
            raise OwnerPackageError(
                f"owner-package source contains forbidden external-content markers: {relative}: {hits}"
            )
        checked.append(relative)
    return {
        **manifest(),
        "validated": True,
        "checked_files": checked,
        "forbidden_content_found": False,
    }


def export_owner_package(repository_root: Path, destination: Path) -> dict[str, Any]:
    report = validate_source_tree(repository_root)
    root = repository_root.resolve()
    target = destination.resolve()
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)

    for relative in OWNER_PACKAGE_FILES:
        output = target / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, output)

    package_manifest = {
        "contract": OWNER_PACKAGE_CONTRACT,
        "package": "file-owner",
        "files": list(OWNER_PACKAGE_FILES),
        "validated": True,
    }
    (target / "OWNER_PACKAGE_MANIFEST.json").write_text(
        json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {**report, "destination": str(target)}


__all__ = [
    "OWNER_PACKAGE_CONTRACT",
    "OWNER_PACKAGE_FILES",
    "OwnerPackageError",
    "export_owner_package",
    "manifest",
    "validate_paths",
    "validate_source_tree",
]
