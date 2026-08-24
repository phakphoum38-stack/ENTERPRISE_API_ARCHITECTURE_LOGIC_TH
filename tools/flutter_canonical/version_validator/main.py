#!/usr/bin/env python3
"""Validate a Flutter pubspec application version."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

VERSION_RE = re.compile(r"^version:\s*([0-9]+)\.([0-9]+)\.([0-9]+)(?:\+([0-9]+))?\s*$")


def validate(pubspec: Path) -> tuple[bool, str]:
    for line in pubspec.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version:"):
            value = line.strip()
            if VERSION_RE.match(value):
                return True, value
            return False, f"invalid version format: {value}"
    return False, "version field not found"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pubspec", nargs="?", default="pubspec.yaml")
    args = parser.parse_args()
    ok, message = validate(Path(args.pubspec))
    print(message)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
