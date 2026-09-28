#!/usr/bin/env python3
"""Deterministic, fail-closed secret-like material scanner for Research OS."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, sys
from pathlib import Path

SCHEMA = "research-os.secret-scan.v1"
DEFAULT_EXTENSIONS = {".py",".ps1",".psm1",".psd1",".yml",".yaml",".json",".toml",".env",".ini",".cfg",".conf",".dart",".php",".ts",".tsx",".js",".jsx",".md",".txt"}
EXCLUDED_DIRS = {".git",".dart_tool","build","dist","node_modules","bin","obj","__pycache__",".pytest_cache",".mypy_cache",".venv","venv","reports","coverage","tmp","temp","cache"}
PLACEHOLDER_VALUES = {"changeme","change-me","example","placeholder","redacted","your-secret","your_secret","your-api-key","your_api_key","dummy","test-secret","test_secret","not-a-secret","not_a_secret"}
SAFE_TEST_VALUES = {"ci-owner-provider-key","wrong-but-long-enough","provider-smoke-secret","candidate-provider-secret"}
PATTERNS = (
 ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
 ("github_token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}\b")),
 ("github_pat", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
 ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
 ("openai_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
 ("generic_secret_assignment", re.compile(r"(?i)\b(api[_-]?key|access[_-]?token|auth[_-]?token|password|secret|client[_-]?secret|private[_-]?key)\b\s*[:=]\s*(?P<quote>['\"])(?P<value>[^'\"\r\n]{16,})(?P=quote)")),
 ("generic_bearer", re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{24,}\b")),
)

def is_efi_path(path: Path) -> bool:
    return any(part.casefold() == "efi" for part in path.parts)

def excluded(path: Path) -> bool:
    return any(part in EXCLUDED_DIRS for part in path.parts) or is_efi_path(path)

def relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()

def candidate_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or excluded(path):
            continue
        if path.suffix.casefold() in DEFAULT_EXTENSIONS or path.name.startswith(".env"):
            yield path

def looks_placeholder(value: str) -> bool:
    normalized = value.strip().strip("<>[]{}()").casefold()
    if normalized in PLACEHOLDER_VALUES or normalized in SAFE_TEST_VALUES:
        return True
    if any(marker in value for marker in (" + ", " = ", "{", "}", "$(")):
        return True
    return any(token in normalized for token in ("example.com","example.org","localhost","127.0.0.1","replace-me","replace_me","insert-","insert_"))

def fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]

def scan_file(root: Path, path: Path) -> list[dict]:
    try:
        text = path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError):
        return []
    findings = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for detector_id, pattern in PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            value = match.groupdict().get("value")
            if value is not None and looks_placeholder(value):
                continue
            findings.append({"detector": detector_id, "path": relative_path(root, path), "line": line_number, "value_fingerprint": fingerprint(value) if value is not None else None})
    return findings

def git_source_sha(root: Path) -> str | None:
    try:
        return subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--source-sha", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(json.dumps({"schema": SCHEMA, "status": "FAIL", "error": "root_not_directory"}))
        return 2
    findings, scanned_files = [], 0
    for path in candidate_files(root):
        scanned_files += 1
        findings.extend(scan_file(root, path))
    findings.sort(key=lambda item: (item["path"], item["line"], item["detector"]))
    report = {"schema": SCHEMA, "status": "FAIL" if findings else "PASS", "source_sha": args.source_sha or git_source_sha(root), "scanned_files": scanned_files, "finding_count": len(findings), "findings": findings, "fail_closed": True, "secret_values_emitted": False, "efi_paths_scanned": False}
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True); output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 1 if findings else 0

if __name__ == "__main__":
    sys.exit(main())
