#!/usr/bin/env python3
"""Bounded platform-wide structural reconciliation and deterministic repair planning.

The module composes existing Platform registries instead of creating a second
authority. It resolves repository-local references, classifies failures, and
produces minimal repair plans. Applying a repair is deliberately explicit and
must occur in an isolated sandbox/branch.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_PLATFORM_SELF_RECONCILIATION_CONTRACT.json"
PROTECTED_PREFIXES = (
    ".github/workflows/",
    "current/RESEARCH_OS_UNIFIED_FINAL_GATE",
    "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json",
    "current/ARCHITECTURE_INVARIANTS.md",
)
LOCAL_PREFIXES = (
    "current/", "tools/", "docs/", "apps/", "owner_special/", "scripts/", ".github/"
)
REFERENCE_RE = re.compile(r'(?:"|\')((' + "|".join(re.escape(p) for p in LOCAL_PREFIXES) + r')[^"\']+)(?:"|\')')


@dataclass(frozen=True)
class PathResolution:
    requested: str
    status: str
    target: str | None
    candidates: tuple[str, ...]


@dataclass(frozen=True)
class RepairPlan:
    repair_id: str
    source_sha: str
    finding: str
    old_reference: str
    resolved_reference: str
    write_set: tuple[str, ...]
    protected_set: tuple[str, ...]
    confidence: str
    reason: str


def tracked_files(root: Path = ROOT) -> tuple[str, ...]:
    """Return the repository's tracked files without depending on git Python APIs."""
    import subprocess

    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(sorted(line.strip() for line in result.stdout.splitlines() if line.strip()))


def _basename_index(paths: Iterable[str]) -> dict[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    for path in paths:
        index.setdefault(Path(path).name, []).append(path)
    return {key: tuple(sorted(value)) for key, value in index.items()}


def resolve_path(reference: str, files: Iterable[str]) -> PathResolution:
    normalized = reference.replace("\\", "/").lstrip("./")
    file_set = set(files)
    if normalized in file_set:
        return PathResolution(reference, "FOUND", normalized, (normalized,))

    candidates = _basename_index(file_set).get(Path(normalized).name, ())
    if len(candidates) == 1:
        return PathResolution(reference, "RELOCATABLE", candidates[0], candidates)
    if len(candidates) > 1:
        return PathResolution(reference, "AMBIGUOUS", None, candidates)
    return PathResolution(reference, "MISSING", None, ())


def is_protected(path: str) -> bool:
    normalized = path.replace("\\", "/").lstrip("./")
    return any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def extract_local_references(text: str) -> tuple[str, ...]:
    return tuple(sorted(set(match.group(1) for match in REFERENCE_RE.finditer(text))))


def reconcile_file(path: str, files: Iterable[str], root: Path = ROOT) -> list[PathResolution]:
    text = (root / path).read_text(encoding="utf-8")
    return [resolve_path(reference, files) for reference in extract_local_references(text)]


def canonical_reconciliation_targets(root: Path = ROOT) -> tuple[str, ...]:
    """Return only existing canonical source documents; no new registry is created."""
    governance = root / "current" / "RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json"
    final_gate = root / "current" / "RESEARCH_OS_UNIFIED_FINAL_GATE.yml"
    registry = root / "current" / "PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json"
    return tuple(
        path for path in (
            "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json",
            "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
            "current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json",
        ) if (root / path).is_file()
    )


def reconcile_sources(root: Path = ROOT) -> dict[str, object]:
    files = tracked_files(root)
    findings: list[dict[str, object]] = []
    for source in canonical_reconciliation_targets(root):
        for resolution in reconcile_file(source, files, root):
            if resolution.status != "FOUND":
                findings.append({
                    "source": source,
                    "reference": resolution.requested,
                    "status": resolution.status,
                    "target": resolution.target,
                    "candidates": list(resolution.candidates),
                })
    return {
        "status": "PASS" if not findings else "DRIFT",
        "sources": list(canonical_reconciliation_targets(root)),
        "finding_count": len(findings),
        "findings": findings,
        "tracked_file_count": len(files),
    }


def build_plan(
    source_sha: str,
    owner_file: str,
    resolution: PathResolution,
) -> RepairPlan:
    if resolution.status != "RELOCATABLE" or resolution.target is None:
        raise ValueError("only uniquely relocatable references may produce an automatic plan")
    protected = (resolution.target,) if is_protected(resolution.target) else ()
    if protected:
        raise ValueError("protected targets cannot be auto-repaired")
    repair_id = "repair-" + hashlib.sha256(
        f"{source_sha}:{owner_file}:{resolution.requested}:{resolution.target}".encode()
    ).hexdigest()[:16]
    return RepairPlan(
        repair_id=repair_id,
        source_sha=source_sha,
        finding="CANONICAL_PATH_RELOCATION",
        old_reference=resolution.requested,
        resolved_reference=resolution.target,
        write_set=(owner_file,),
        protected_set=protected,
        confidence="DETERMINISTIC",
        reason="exactly one tracked file matches the requested basename",
    )


def replace_reference(text: str, plan: RepairPlan) -> str:
    if plan.old_reference not in text:
        raise ValueError("repair reference is no longer present")
    return text.replace(plan.old_reference, plan.resolved_reference)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference")
    parser.add_argument("--file")
    parser.add_argument("--source-sha", default="UNKNOWN")
    parser.add_argument("--scan", action="store_true")
    args = parser.parse_args()

    if args.scan:
        print(json.dumps(reconcile_sources(), sort_keys=True))
        return 0 if reconcile_sources()["status"] == "PASS" else 1

    files = tracked_files()
    if args.reference:
        resolution = resolve_path(args.reference, files)
        print(json.dumps({
            "reference": args.reference,
            "status": resolution.status,
            "target": resolution.target,
            "candidates": resolution.candidates,
        }, sort_keys=True))
        if args.file and resolution.status == "RELOCATABLE":
            plan = build_plan(args.source_sha, args.file, resolution)
            print(json.dumps(plan.__dict__, sort_keys=True))
        return 0 if resolution.status in {"FOUND", "RELOCATABLE"} else 1

    print(json.dumps({
        "status": "PASS",
        "tracked_files": len(files),
        "contract": str(CONTRACT.relative_to(ROOT)),
        "protected_prefixes": list(PROTECTED_PREFIXES),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
