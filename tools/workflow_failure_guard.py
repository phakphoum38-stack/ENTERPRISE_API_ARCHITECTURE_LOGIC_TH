#!/usr/bin/env python3
"""Guard investigation-issue creation against duplicate and bursty failures."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timedelta, timezone


def gh(args: list[str]) -> str:
    return subprocess.check_output(["gh", *args], text=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--workflow", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--classification", required=True)
    p.add_argument("--limit", type=int, default=3)
    p.add_argument("--window-minutes", type=int, default=60)
    args = p.parse_args()

    material = f"{args.workflow}|{args.classification}".encode()
    fingerprint = hashlib.sha256(material).hexdigest()
    title = f"Workflow Intelligence: {args.workflow} {args.classification} fingerprint:{fingerprint}"
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=args.window_minutes)

    existing = json.loads(gh(["issue", "list", "--state", "all", "--limit", "20", "--json", "title,createdAt"]))
    duplicate = any(item.get("title") == title for item in existing)
    recent = 0
    for item in existing:
        created = item.get("createdAt")
        if not created:
            continue
        try:
            when = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            continue
        if when >= cutoff and str(item.get("title", "")).startswith("Workflow Intelligence:"):
            recent += 1

    allowed = not duplicate and recent < args.limit
    result = {
        "version": 1,
        "fingerprint": fingerprint,
        "duplicate": duplicate,
        "recent_investigation_issues": recent,
        "rate_limit": {"max": args.limit, "window_minutes": args.window_minutes},
        "allowed": allowed,
        "reason": "DUPLICATE" if duplicate else ("RATE_LIMIT" if recent >= args.limit else "ALLOW"),
        "issue_title": title,
    }
    print(json.dumps(result, indent=2))
    return 0 if allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
