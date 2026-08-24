#!/usr/bin/env python3
"""Conservative validator for GitHub Actions workflow files."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

NAME_RE = re.compile(r"^name:\s*.+$", re.M)
ON_RE = re.compile(r"^(?:on|'on'):\s*(?:$|.+)$", re.M)
JOBS_RE = re.compile(r"^jobs:\s*$", re.M)
JOB_KEY_RE = re.compile(r"^  [A-Za-z0-9_.-]+:\s*$", re.M)


def validate(path: Path) -> tuple[bool, list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    errors: list[str] = []
    if not NAME_RE.search(text):
        errors.append("missing top-level name")
    if not ON_RE.search(text):
        errors.append("missing top-level on")
    if not JOBS_RE.search(text):
        errors.append("missing jobs section")
    elif not JOB_KEY_RE.search(text.split("jobs:", 1)[1]):
        errors.append("jobs section has no obvious job key")
    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".github/workflows")
    args = parser.parse_args()
    root = Path(args.root)
    files = sorted(list(root.glob("*.yml")) + list(root.glob("*.yaml"))) if root.is_dir() else [root]
    if not files:
        print("no workflow files found")
        return 1
    failed = False
    for path in files:
        ok, errors = validate(path)
        print(f"{'PASS' if ok else 'FAIL'} {path}")
        for error in errors:
            print(f"  - {error}")
        failed |= not ok
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
