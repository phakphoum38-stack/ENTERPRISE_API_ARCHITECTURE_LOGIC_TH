#!/usr/bin/env python3
"""Validate Research OS GUI/UX design asset manifest and repository assets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "manifest" / "assets.json"
ALLOWED = {"png", "psd", "jpg", "jpeg", "svg"}
FORBIDDEN_NAMES = {".DS_Store", "Thumbs.db"}


def main() -> int:
    if not MANIFEST.exists():
        print(f"ERROR: missing manifest: {MANIFEST}")
        return 1

    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON manifest: {exc}")
        return 1

    if data.get("schema") != "research-os.gui-asset-manifest":
        print("ERROR: unsupported manifest schema")
        return 1

    assets = data.get("assets")
    if not isinstance(assets, list):
        print("ERROR: manifest.assets must be a list")
        return 1

    seen = set()
    errors = []
    for item in assets:
        if not isinstance(item, dict):
            errors.append("asset entry must be an object")
            continue
        path_value = item.get("path")
        if not isinstance(path_value, str) or not path_value:
            errors.append("asset entry requires a non-empty path")
            continue
        path = Path(path_value)
        if path.is_absolute() or ".." in path.parts:
            errors.append(f"unsafe asset path: {path_value}")
            continue
        if path_value in seen:
            errors.append(f"duplicate asset path: {path_value}")
        seen.add(path_value)

        suffix = path.suffix.lower().lstrip(".")
        if suffix not in ALLOWED:
            errors.append(f"unsupported asset type: {path_value}")
        if path.name in FORBIDDEN_NAMES:
            errors.append(f"temporary/system file is forbidden: {path_value}")
        if not path_value.startswith("design/"):
            errors.append(f"asset must live under design/: {path_value}")

        repo_path = ROOT.parent / path.relative_to("design") if path.parts[0] == "design" else ROOT / path
        if not repo_path.exists():
            errors.append(f"manifest references missing file: {path_value}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: validated {len(assets)} manifest asset(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
