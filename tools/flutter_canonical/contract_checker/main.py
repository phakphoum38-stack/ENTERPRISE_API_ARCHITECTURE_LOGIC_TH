#!/usr/bin/env python3
"""Check that repository contracts contain required headings/markers."""
from __future__ import annotations

import argparse
from pathlib import Path

DEFAULT_MARKERS = ("Version", "Execution", "Runner", "Security")


def check(path: Path, markers: tuple[str, ...]) -> tuple[bool, list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    missing = [marker for marker in markers if marker.lower() not in text.lower()]
    return not missing, missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--marker", action="append", dest="markers")
    args = parser.parse_args()
    path = Path(args.path)
    markers = tuple(args.markers) if args.markers else DEFAULT_MARKERS
    ok, missing = check(path, markers)
    print(f"{'PASS' if ok else 'FAIL'} {path}")
    for marker in missing:
        print(f"  - missing marker: {marker}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
