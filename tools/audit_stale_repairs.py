#!/usr/bin/env python3
"""Detect stale or duplicate repair PRs without mutating repository state."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--output", default="reports/STALE_REPAIR_AUDIT.json")
    args = p.parse_args()
    raw = subprocess.check_output(["gh", "pr", "list", "--state", "open", "--limit", "100", "--json", "number,title,headRefName,updatedAt"], text=True)
    prs = json.loads(raw)
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    candidates = []
    fingerprints: dict[str, list[int]] = {}
    for pr in prs:
        branch = str(pr.get("headRefName", ""))
        if not (branch.startswith("repair/") or branch.startswith("auto-repair/") or "workflow-intelligence" in branch):
            continue
        updated = datetime.fromisoformat(str(pr["updatedAt"]).replace("Z", "+00:00"))
        key = str(pr.get("title", "")).split("fingerprint:")[-1].strip()
        if key:
            fingerprints.setdefault(key, []).append(int(pr["number"]))
        candidates.append({"number": pr["number"], "title": pr["title"], "head_ref": branch, "updated_at": pr["updatedAt"], "stale": updated < cutoff})
    duplicates = [nums for nums in fingerprints.values() if len(nums) > 1]
    result = {"version": 1, "policy": {"stale_after_days": args.days, "mutate_automatically": False}, "candidates": candidates, "stale": [x for x in candidates if x["stale"]], "duplicate_fingerprint_prs": duplicates, "status": "CLEAN" if not any(x["stale"] for x in candidates) and not duplicates else "REVIEW_REQUIRED"}
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
