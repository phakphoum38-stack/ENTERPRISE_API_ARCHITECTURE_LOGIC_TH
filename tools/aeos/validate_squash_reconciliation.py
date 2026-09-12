#!/usr/bin/env python3
"""Validate explicit AEOS squash-reconciliation provenance."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def run_bytes(*args: str) -> bytes:
    return subprocess.check_output(args)


def run(*args: str) -> str:
    return run_bytes(*args).decode("utf-8").strip()


def changed_paths(a: str, b: str) -> set[str]:
    return {line for line in run("git", "diff", "--name-only", a, b).splitlines() if line}


def path_patch(a: str, b: str, path: str) -> bytes:
    return run_bytes("git", "diff", "--no-ext-diff", "--binary", a, b, "--", path)


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: validate_squash_reconciliation.py MANIFEST.json [source|forensic]", file=sys.stderr)
        return 2
    stage = sys.argv[2] if len(sys.argv) == 3 else "forensic"
    if stage not in {"source", "forensic"}:
        raise SystemExit("FAIL: unsupported validation stage")

    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    required = {
        "schema", "pr_number", "base_sha", "head_sha", "merge_sha",
        "merge_parent_sha", "divergent_paths", "canonical_conflict_evidence",
        "accepted_payload_paths", "accepted_payload_digest",
        "independent_forensic_status", "merge_authority", "self_certification",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise SystemExit(f"FAIL: missing reconciliation fields: {missing}")
    if data["schema"] != "aeos.squash-reconciliation.v1":
        raise SystemExit("FAIL: unsupported reconciliation schema")
    if data["merge_authority"] is not False or data["self_certification"] is not False:
        raise SystemExit("FAIL: reconciliation evidence cannot grant authority or self-certify")
    if stage == "forensic" and data["independent_forensic_status"] != "VERIFIED":
        raise SystemExit("FAIL: independent forensic verification is required")

    base = data["base_sha"]
    head = data["head_sha"]
    merge = data["merge_sha"]
    parents = run("git", "rev-list", "--parents", "-n", "1", merge).split()[1:]
    if parents != [data["merge_parent_sha"]] or parents != [base]:
        raise SystemExit("FAIL: squash merge must have exactly BASE as its only parent")

    head_paths = changed_paths(base, head)
    merge_paths = changed_paths(base, merge)
    divergent = {
        path for path in head_paths | merge_paths
        if path_patch(base, head, path) != path_patch(base, merge, path)
    }
    declared = set(data["divergent_paths"])
    if divergent != declared:
        raise SystemExit(f"FAIL: divergent path inventory mismatch: actual={sorted(divergent)} declared={sorted(declared)}")

    evidence = data["canonical_conflict_evidence"]
    if set(evidence) != declared:
        raise SystemExit("FAIL: every divergent path needs canonical conflict evidence")
    for path in sorted(declared):
        item = evidence[path]
        if not item.get("stale_or_conflicting") or not item.get("evidence"):
            raise SystemExit(f"FAIL: incomplete stale/conflict proof for divergent path: {path}")

    accepted = set(data["accepted_payload_paths"])
    if accepted != merge_paths:
        raise SystemExit(f"FAIL: accepted payload inventory mismatch: actual={sorted(merge_paths)} declared={sorted(accepted)}")

    merge_tree = run("git", "rev-parse", f"{merge}^{{tree}}")
    if merge_tree != data["accepted_payload_digest"]:
        raise SystemExit("FAIL: accepted payload digest/tree identity mismatch")
    if run("git", "merge-base", base, merge) != base:
        raise SystemExit("FAIL: merge is not based on canonical BASE")

    print(json.dumps({
        "status": "PASS",
        "stage": stage,
        "schema": data["schema"],
        "pr_number": data["pr_number"],
        "base_sha": base,
        "head_sha": head,
        "merge_sha": merge,
        "divergent_paths": sorted(declared),
        "accepted_payload_paths": sorted(accepted),
        "accepted_payload_digest": merge_tree,
        "independent_forensic_status": data["independent_forensic_status"],
        "merge_authority": data["merge_authority"],
        "self_certification": data["self_certification"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
