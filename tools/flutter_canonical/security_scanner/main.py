#!/usr/bin/env python3
"""Conservative secret-like scanner. Findings require human review."""
from __future__ import annotations

import argparse
import re
from pathlib import Path

EXTENSIONS = {".py", ".md", ".yml", ".yaml", ".json", ".toml", ".dart", ".env"}
EXCLUDES = {".git", ".dart_tool", "build", "reports", "__pycache__"}
PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|password|secret)\s*[:=]\s*['\"]([^'\"]{8,})['\"]"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)


def scan(root: Path) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in EXTENSIONS or any(p in EXCLUDES for p in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in PATTERNS:
            if pattern.search(text):
                findings.append((path.relative_to(root).as_posix(), pattern.pattern))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    findings = scan(Path(args.root).resolve())
    if not findings:
        print("PASS no secret-like matches")
        return 0
    print("REVIEW required: secret-like matches found")
    for path, pattern in findings:
        print(f"- {path}: {pattern}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
