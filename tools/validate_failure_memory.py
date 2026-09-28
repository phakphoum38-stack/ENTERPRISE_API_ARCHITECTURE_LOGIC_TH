#!/usr/bin/env python3
"""Validate that failure memory contains only explicitly verified fixes."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SHA = re.compile(r"^[0-9a-f]{40}$")
FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")
REQUIRED = {"fingerprint", "classification", "root_cause", "verified_fix", "verified_commit"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--memory", default="current/WORKFLOW_FAILURE_MEMORY.json")
    p.add_argument("--output", default="reports/FAILURE_MEMORY_VALIDATION.json")
    args = p.parse_args()
    data = json.loads(Path(args.memory).read_text(encoding="utf-8"))
    errors = []
    if data.get("policy", {}).get("only_verified") is not True:
        errors.append("memory policy must require verified entries")
    entries = data.get("entries")
    if not isinstance(entries, list):
        errors.append("entries must be a list")
        entries = []
    seen = set()
    for i, entry in enumerate(entries):
        missing = REQUIRED - set(entry)
        if missing:
            errors.append(f"entry {i} missing: {sorted(missing)}")
            continue
        fp = str(entry["fingerprint"]).lower()
        commit = str(entry["verified_commit"]).lower()
        if not FINGERPRINT.fullmatch(fp):
            errors.append(f"entry {i} fingerprint is not SHA256")
        if not SHA.fullmatch(commit):
            errors.append(f"entry {i} verified_commit is not a commit SHA")
        if entry.get("verified") is not True:
            errors.append(f"entry {i} is not explicitly verified")
        if fp in seen:
            errors.append(f"duplicate fingerprint: {fp}")
        seen.add(fp)
    result = {"version": 1, "status": "PASS" if not errors else "FAIL", "entries": len(entries), "errors": errors}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
