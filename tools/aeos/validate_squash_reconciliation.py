#!/usr/bin/env python3
"""Validate explicit AEOS squash-reconciliation provenance.

The validator never decides that a divergent path is stale by itself. The
manifest must enumerate the divergence and provide externally reviewable
reasons/evidence. The validator only proves structural and cryptographic
constraints and fails closed on missing or inconsistent evidence.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True).strip()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def diff_names(a: str, b: str) -> set[str]:
    out = run("git", "diff", "--name-only", a, b)
    return {line for line in out.splitlines() if line}


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_squash_reconciliation.py MANIFEST.json", file=sys.stderr)
        return 2

    manifest_path = Path(sys.argv[1])
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
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
    if data["independent_forensic_status"] != "VERIFIED":
        raise SystemExit("FAIL: independent forensic verification is required")

    base = data["base_sha"]
    head = data["head_sha"]
    merge = data["merge_sha"]
    merge_parents = run("git", "rev-list", "--parents", "-n", "1", merge).split()[1:]
    if merge_parents != [data["merge_parent_sha"]] or merge_parents != [base]:
        raise SystemExit("FAIL: squash merge must have exactly BASE as its only parent")

    actual_divergence = diff_names(base, head) - diff_names(base, merge)
    declared = set(data["divergent_paths"])
    if actual_divergence != declared:
        raise SystemExit(
            "FAIL: divergent path inventory mismatch: "
            f"actual={sorted(actual_divergence)} declared={sorted(declared)}"
        )

    conflict_evidence = data["canonical_conflict_evidence"]
    if set(conflict_evidence) != declared:
        raise SystemExit("FAIL: every divergent path needs canonical conflict evidence")
    for path in sorted(declared):
        item = conflict_evidence[path]
        if not item.get("stale_or_conflicting"):
            raise SystemExit(f"FAIL: path is not proven stale/conflicting: {path}")
        if not item.get("evidence"): 
            raise SystemExit(f"FAIL: missing evidence reference for divergent path: {path}")

    accepted = set(data["accepted_payload_paths"])
    actual_merge = diff_names(base, merge)
    if accepted != actual_merge:
        raise SystemExit(
            "FAIL: accepted payload inventory mismatch: "
            f"actual={sorted(actual_merge)} declared={sorted(accepted)}"
        )

    digest_files = [run("git", "ls-tree", "-r", "--name-only", merge)]
    payload_digest = hashlib.sha256("\n".join(digest_files).encode()).hexdigest()
    if payload_digest != data["accepted_payload_digest"]:
        raise SystemExit("FAIL: accepted payload digest mismatch")

    if run("git", "merge-base", base, merge) != base:
        raise SystemExit("FAIL: merge is not based on canonical BASE")

    print("PASS: squash reconciliation provenance is structurally valid and fail-closed")
    print(json.dumps({
        "schema": data["schema"],
        "pr_number": data["pr_number"],
        "base_sha": base,
        "head_sha": head,
        "merge_sha": merge,
        "divergent_paths": sorted(declared),
        "accepted_payload_paths": sorted(accepted),
        "independent_forensic_status": data["independent_forensic_status"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
