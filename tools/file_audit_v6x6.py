#!/usr/bin/env python3
"""Adaptive 6^6 repository file audit assistant.

The 6^6 figure is a logical orchestration capacity (46,656 leaf slots), not a
promise to spawn 46,656 OS processes/threads. Runtime concurrency is bounded by
CPU and the number of files so the auditor remains safe on developer machines
and CI runners.
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

BRANCHING_FACTOR = 6
DEPTH = 6
MAX_LEAF_CAPACITY = BRANCHING_FACTOR ** DEPTH

DEFAULT_EXCLUDES = {
    ".git", ".dart_tool", ".idea", ".vscode", "build", "dist",
    "node_modules", "__pycache__", ".venv", "venv",
}

TEXT_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".css", ".dart", ".go", ".h", ".hpp",
    ".html", ".ini", ".java", ".js", ".json", ".kt", ".md", ".ps1", ".py",
    ".rs", ".sh", ".toml", ".ts", ".tsx", ".txt", ".xml", ".yaml", ".yml",
}

# Match actual Git conflict-marker blocks, not decorative separators such as
# "================================" commonly used in plain-text documents.
MERGE_START_RE = re.compile(r"^<<<<<<<(?:\s.*)?$")
MERGE_SEPARATOR_RE = re.compile(r"^=======$")
MERGE_END_RE = re.compile(r"^>>>>>>>(?:\s.*)?$")
SECRET_PATTERNS = (
    ("openai-key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("bearer-token", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}\b", re.I)),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
)


@dataclass(frozen=True)
class Finding:
    path: str
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class FileResult:
    path: str
    findings: tuple[Finding, ...]


def logical_capacity() -> dict[str, int]:
    return {
        "branching_factor": BRANCHING_FACTOR,
        "depth": DEPTH,
        "max_leaf_capacity": MAX_LEAF_CAPACITY,
    }


def _is_excluded(path: Path, root: Path, excludes: set[str]) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in excludes for part in rel.parts)


def discover_files(root: Path, excludes: set[str] | None = None) -> list[Path]:
    root = root.resolve()
    excludes = set(DEFAULT_EXCLUDES if excludes is None else excludes)
    files: list[Path] = []
    for current, dirnames, filenames in os.walk(root):
        current_path = Path(current)
        dirnames[:] = [
            name for name in dirnames
            if name not in excludes and not _is_excluded(current_path / name, root, excludes)
        ]
        for name in filenames:
            path = current_path / name
            if not _is_excluded(path, root, excludes):
                files.append(path)
    return files


def _read_text(path: Path) -> str | None:
    if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"Dockerfile", "Makefile"}:
        return None
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw[:8192]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def _has_unresolved_merge_markers(text: str) -> bool:
    """Return True only for Git conflict markers, not standalone separators."""
    in_conflict = False
    for line in text.splitlines():
        if MERGE_START_RE.fullmatch(line):
            in_conflict = True
            continue
        if MERGE_END_RE.fullmatch(line):
            return True
        if in_conflict and MERGE_SEPARATOR_RE.fullmatch(line):
            continue
    return in_conflict


def audit_file(path: Path, root: Path) -> FileResult:
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    findings: list[Finding] = []
    try:
        size = path.stat().st_size
    except OSError as exc:
        return FileResult(rel, (Finding(rel, "error", "unreadable", f"Cannot stat file: {exc}"),))
    if size == 0:
        findings.append(Finding(rel, "warning", "empty-file", "File is empty."))
    text = _read_text(path)
    if text is None:
        return FileResult(rel, tuple(findings))
    if "\ufffd" in text:
        findings.append(
            Finding(rel, "warning", "utf8-replacement", "File contains invalid UTF-8 bytes.")
        )

    if _has_unresolved_merge_markers(text):
        findings.append(
            Finding(rel, "error", "merge-marker", "Unresolved Git merge marker found.")
        )

    for code, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            findings.append(Finding(rel, "error", code, "Credential-like material found; verify and remove or rotate if real."))
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            json.loads(text)
        except json.JSONDecodeError as exc:
            findings.append(Finding(rel, "error", "invalid-json", f"JSON parse error: {exc.msg} at line {exc.lineno}."))
    elif suffix == ".py":
        try:
            ast.parse(text, filename=rel)
        except SyntaxError as exc:
            findings.append(Finding(rel, "error", "python-syntax", f"Python syntax error at line {exc.lineno}: {exc.msg}"))
    return FileResult(rel, tuple(findings))


def audit_repository(root: Path, workers: int | None = None) -> dict[str, object]:
    root = root.resolve()
    files = discover_files(root)
    cpu = os.cpu_count() or 2
    worker_count = workers or min(32, max(2, cpu * 2), max(1, len(files)))
    worker_count = max(1, min(worker_count, MAX_LEAF_CAPACITY, max(1, len(files))))
    results: list[FileResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = [pool.submit(audit_file, path, root) for path in files]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    results.sort(key=lambda item: item.path)
    findings = [finding for result in results for finding in result.findings]
    errors = sum(1 for finding in findings if finding.severity == "error")
    warnings = sum(1 for finding in findings if finding.severity == "warning")
    return {
        "schema_version": 1,
        "contract": "adaptive-file-audit-v6x6",
        "capacity": logical_capacity(),
        "runtime_workers": worker_count,
        "files_scanned": len(files),
        "findings_total": len(findings),
        "errors": errors,
        "warnings": warnings,
        "findings": [asdict(item) for item in findings],
    }


def _print_human(report: dict[str, object]) -> None:
    capacity = report["capacity"]
    print("Research OS File Audit v6^6")
    print(f"Logical leaf capacity: {capacity['max_leaf_capacity']:,}")
    print(f"Runtime workers: {report['runtime_workers']}")
    print(f"Files scanned: {report['files_scanned']}")
    print(f"Errors: {report['errors']}  Warnings: {report['warnings']}")
    for finding in report["findings"]:
        print(f"[{finding['severity'].upper()}] {finding['path']} ({finding['code']}): {finding['message']}")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Adaptive 6^6 repository file audit")
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan")
    parser.add_argument("--workers", type=int, default=None, help="Bounded runtime worker count")
    parser.add_argument("--json", dest="json_path", help="Write full JSON report to this path")
    parser.add_argument("--fail-on-warning", action="store_true", help="Return non-zero when warnings are present as well as errors")
    args = parser.parse_args(list(argv) if argv is not None else None)
    report = audit_repository(Path(args.root), workers=args.workers)
    _print_human(report)
    if args.json_path:
        output = Path(args.json_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if int(report["errors"]) > 0:
        return 2
    if args.fail_on_warning and int(report["warnings"]) > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
