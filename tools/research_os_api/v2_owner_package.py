#!/usr/bin/env python3
"""Build and validate the standalone Research OS file-owner package."""

from __future__ import annotations

import ast
import json
import shutil
from pathlib import Path
from typing import Any, Iterable


OWNER_PACKAGE_CONTRACT = "research-os-file-owner-package-v2"
OWNER_PACKAGE_FILES = (
    "tools/research_os_api/v2_file_ownership_boundary.py",
)
_ALLOWED_IMPORT_ROOTS = {"__future__", "typing"}


class OwnerPackageError(RuntimeError):
    pass


def manifest() -> dict[str, Any]:
    return {
        "contract": OWNER_PACKAGE_CONTRACT,
        "package": "file-owner",
        "files": list(OWNER_PACKAGE_FILES),
        "exact_allowlist": True,
        "standalone": True,
        "extra_subsystems_included": False,
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
    return normalized


def _validate_imports(source_text: str, relative: str) -> None:
    try:
        tree = ast.parse(source_text, filename=relative)
    except SyntaxError as exc:
        raise OwnerPackageError(f"invalid owner-package source: {relative}: {exc}") from exc

    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_roots.add((node.module or "").split(".", 1)[0])

    unexpected = sorted(root for root in imported_roots if root not in _ALLOWED_IMPORT_ROOTS)
    if unexpected:
        raise OwnerPackageError(
            f"owner-package source has dependencies outside the standalone allowlist: {relative}: {unexpected}"
        )


def validate_source_tree(repository_root: Path) -> dict[str, Any]:
    root = repository_root.resolve()
    validate_paths(OWNER_PACKAGE_FILES)
    checked: list[str] = []
    for relative in OWNER_PACKAGE_FILES:
        source = (root / relative).resolve()
        if not source.is_file() or root not in source.parents:
            raise OwnerPackageError(f"owner-package source missing or outside repository: {relative}")
        text = source.read_text(encoding="utf-8")
        _validate_imports(text, relative)
        checked.append(relative)
    return {
        **manifest(),
        "validated": True,
        "checked_files": checked,
        "unexpected_dependencies_found": False,
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
        "standalone": True,
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
