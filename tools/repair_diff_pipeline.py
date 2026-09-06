#!/usr/bin/env python3
"""Create, validate, and optionally apply bounded Autobot repair diffs.

A repair diff is an auditable proposal. This module never pushes, merges, or
changes protected release gates. Applying a diff is an explicit local/runner
operation and is kept separate from diff generation and validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

PROTECTED_PATH_PARTS = {
    ".github/workflows/release.yml",
    ".github/workflows/canonical-source-lineage-gate.yml",
    ".github/workflows/owner-special-friend.yml",
    "owner_special/scripts/verify-installed-owner-provenance.ps1",
}
MAX_DIFF_BYTES = 250_000
MAX_FILES = 25
MAX_HUNKS = 250


def _paths(diff: str) -> list[str]:
    paths: list[str] = []
    for line in diff.splitlines():
        match = re.match(r"^(?:---|\+\+\+) ([ab]/)(.+)$", line)
        if not match:
            continue
        path = match.group(2)
        if path != "/dev/null" and path not in paths:
            paths.append(path)
    return paths


def validate_diff(diff: str) -> dict[str, object]:
    errors: list[str] = []
    raw = diff.encode("utf-8")
    if not raw.strip():
        errors.append("repair diff is empty")
    if len(raw) > MAX_DIFF_BYTES:
        errors.append(f"repair diff exceeds {MAX_DIFF_BYTES} bytes")

    paths = _paths(diff)
    if not paths and raw.strip():
        errors.append("no unified-diff file headers found")
    if len(paths) > MAX_FILES:
        errors.append(f"repair touches more than {MAX_FILES} files")

    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
            errors.append(f"unsafe diff path: {path}")
        if normalized in PROTECTED_PATH_PARTS:
            errors.append(f"protected file cannot be auto-repaired: {path}")

    hunk_count = sum(1 for line in diff.splitlines() if line.startswith("@@"))
    if hunk_count > MAX_HUNKS:
        errors.append(f"repair exceeds maximum {MAX_HUNKS} hunks")

    return {
        "version": 1,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "files": paths,
        "file_count": len(paths),
        "hunk_count": hunk_count,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
        "apply_to_main": False,
        "auto_merge": False,
    }


def apply_diff(diff_path: Path) -> None:
    validation = validate_diff(diff_path.read_text(encoding="utf-8"))
    if validation["status"] != "PASS":
        raise ValueError("cannot apply invalid repair diff: " + "; ".join(validation["errors"]))
    subprocess.run(["git", "apply", "--check", str(diff_path)], check=True)
    subprocess.run(["git", "apply", str(diff_path)], check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff", required=True, help="unified diff file")
    parser.add_argument("--output", help="validation JSON output")
    parser.add_argument("--apply", action="store_true", help="explicitly apply after validation")
    args = parser.parse_args()

    diff_path = Path(args.diff)
    validation = validate_diff(diff_path.read_text(encoding="utf-8"))
    if args.apply and validation["status"] == "PASS":
        apply_diff(diff_path)
        validation["applied"] = True
    else:
        validation["applied"] = False

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(validation, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(validation, indent=2))
    return 0 if validation["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
