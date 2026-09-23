#!/usr/bin/env python3
"""Fail-closed AEOS changed-file lineage verifier.

Every changed path must be explainable by one of:
- existing lineage (modified)
- rename/move lineage
- copy lineage
- explicit predecessor
- explicit genesis/new-artifact declaration

Filename similarity alone is never sufficient.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class Result:
    status: str
    path: str
    file: str
    fail_code: str | None
    reason: str
    lineage_root: str | None
    expected_parent: str | None
    actual_source: str | None
    head_sha: str
    base_sha: str
    severity: str
    gate: str
    evidence: list[str]
    resolution: str | None = None


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def changed(repo: Path, base: str, head: str) -> list[list[str]]:
    raw = git(repo, "diff", "--name-status", "--find-renames=50%", "--find-copies=50%", base, head)
    rows: list[list[str]] = []
    for line in raw.splitlines():
        if not line:
            continue
        parts = line.split("\t")
        rows.append(parts)
    return rows


def load_manifest(path: Path | None) -> dict:
    if path is None:
        return {"entries": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != 1 or not isinstance(data.get("entries"), dict):
        raise ValueError("AEOS lineage manifest must use version=1 and an entries object")
    return data


def result_for(
    *,
    status: str,
    path: str,
    file: str,
    head: str,
    base: str,
    reason: str,
    evidence: list[str],
    lineage_root: str | None = None,
    expected_parent: str | None = None,
    actual_source: str | None = None,
    fail_code: str | None = None,
    severity: str = "INFO",
    resolution: str | None = None,
) -> Result:
    return Result(
        status=status,
        path=path,
        file=file,
        fail_code=fail_code,
        reason=reason,
        lineage_root=lineage_root,
        expected_parent=expected_parent,
        actual_source=actual_source,
        head_sha=head,
        base_sha=base,
        severity=severity,
        gate="AEOS-LINEAGE",
        evidence=evidence,
        resolution=resolution,
    )


def verify(repo: Path, base: str, head: str, manifest: dict) -> list[Result]:
    entries = manifest["entries"]
    out: list[Result] = []

    for row in changed(repo, base, head):
        status = row[0]
        if status.startswith("R") and len(row) >= 3:
            old_path, new_path = row[1], row[2]
            entry = entries.get(new_path) or entries.get(old_path)
            out.append(
                result_for(
                    status="RENAMED",
                    path=new_path,
                    file=new_path,
                    head=head,
                    base=base,
                    reason="Git rename detection provides an explicit predecessor.",
                    evidence=[f"git rename {old_path} -> {new_path}", f"base={base}", f"head={head}"],
                    lineage_root=(entry or {}).get("lineage_root") if isinstance(entry, dict) else old_path,
                    expected_parent=old_path,
                    actual_source=old_path,
                )
            )
            continue

        if status.startswith("C") and len(row) >= 3:
            old_path, new_path = row[1], row[2]
            entry = entries.get(new_path)
            out.append(
                result_for(
                    status="COPIED",
                    path=new_path,
                    file=new_path,
                    head=head,
                    base=base,
                    reason="Git copy detection provides an explicit source.",
                    evidence=[f"git copy {old_path} -> {new_path}", f"base={base}", f"head={head}"],
                    lineage_root=(entry or {}).get("lineage_root") if isinstance(entry, dict) else old_path,
                    expected_parent=old_path,
                    actual_source=old_path,
                )
            )
            continue

        path = row[-1]
        if status.startswith("M"):
            out.append(
                result_for(
                    status="MODIFIED",
                    path=path,
                    file=path,
                    head=head,
                    base=base,
                    reason="Path exists on both base and head; existing lineage is preserved.",
                    evidence=[f"path exists in base and head: {path}", f"base={base}", f"head={head}"],
                    lineage_root=path,
                )
            )
            continue

        if status.startswith("A"):
            entry = entries.get(path)
            if isinstance(entry, dict) and entry.get("kind") in {"predecessor", "genesis"}:
                kind = entry["kind"]
                parent = entry.get("predecessor")
                root = entry.get("lineage_root") or (parent if kind == "predecessor" else path)
                if kind == "predecessor" and not parent:
                    out.append(
                        result_for(
                            status="ORPHAN_ADDED",
                            path=path,
                            file=path,
                            head=head,
                            base=base,
                            reason="Explicit predecessor declaration is missing its predecessor path.",
                            evidence=["manifest entry present but predecessor is absent"],
                            fail_code="AEOS-LINEAGE-MISSING-PREDECESSOR",
                            severity="BLOCKING",
                            resolution="Declare a concrete predecessor path or a valid genesis declaration.",
                        )
                    )
                else:
                    out.append(
                        result_for(
                            status="ADDED_WITH_LINEAGE" if kind == "predecessor" else "ADDED_GENESIS",
                            path=path,
                            file=path,
                            head=head,
                            base=base,
                            reason="Explicit AEOS lineage declaration supplied.",
                            evidence=[f"manifest kind={kind}", f"base={base}", f"head={head}"],
                            lineage_root=root,
                            expected_parent=parent,
                            actual_source=parent,
                        )
                    )
            else:
                out.append(
                    result_for(
                        status="ORPHAN_ADDED",
                        path=path,
                        file=path,
                        head=head,
                        base=base,
                        reason="New file has no explicit predecessor/genesis evidence.",
                        evidence=[f"added path={path}", f"base={base}", f"head={head}"],
                        fail_code="AEOS-LINEAGE-ORPHAN",
                        severity="BLOCKING",
                        resolution="Add an explicit AEOS lineage manifest entry with predecessor or genesis evidence.",
                    )
                )
            continue

        out.append(
            result_for(
                status="ORPHAN_ADDED",
                path=path,
                file=path,
                head=head,
                base=base,
                reason=f"Unsupported git change status: {status}",
                evidence=[f"git status={status}", f"base={base}", f"head={head}"],
                fail_code="AEOS-LINEAGE-UNKNOWN-CHANGE",
                severity="BLOCKING",
                resolution="Provide explicit lineage evidence for this change type.",
            )
        )

    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--manifest")
    ap.add_argument("--json-out")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    manifest = load_manifest(Path(args.manifest).resolve() if args.manifest else None)
    results = verify(repo, args.base, args.head, manifest)
    blocked = any(item.severity == "BLOCKING" for item in results)
    payload = {
        "schema": "aeos.file-lineage.v1",
        "status": "BLOCKED" if blocked else "PASS",
        "base_sha": args.base,
        "head_sha": args.head,
        "results": [asdict(item) for item in results],
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 1 if blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
