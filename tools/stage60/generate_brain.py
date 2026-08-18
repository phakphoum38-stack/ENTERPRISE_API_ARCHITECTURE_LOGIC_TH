#!/usr/bin/env python3
"""Stage 60 Generate Brain.

Deterministic planning/orchestration helper. 20^20 is logical capacity only;
execution remains bounded by the configured worker limit.
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
from pathlib import Path

LOGICAL_CAPACITY = 20 ** 20
DEFAULT_WORKERS = 4

REQUIRED_CONTRACTS = {
    "ai_chat_ui": ["apps/research_os_flutter/lib/src/features/chat/chat_page.dart"],
    "api_client": ["apps/research_os_flutter/lib/src/api/research_os_api_client.dart"],
    "chat_e2e": ["apps/research_os_flutter/tool/chat_service_e2e.dart"],
    "preflight": ["tools/research_os_api/stage60_preflight.py"],
    "browser_smoke": [".github/workflows/browser-use-cloud-smoke.yml"],
}


def exists(root: Path, path: str) -> bool:
    return (root / path).is_file()


def git_branch(root: Path) -> str:
    try:
        return subprocess.check_output(["git", "branch", "--show-current"], cwd=root, text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="stage60-generate-brain.json")
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    args = parser.parse_args()

    root = Path(args.root).resolve()
    workers = max(1, min(args.workers, 32))
    checks = []
    for name, paths in REQUIRED_CONTRACTS.items():
        checks.append({"name": name, "required": paths, "present": all(exists(root, p) for p in paths)})

    failures = [c["name"] for c in checks if not c["present"]]
    plan = {
        "stage": 60,
        "mode": "generate-brain",
        "branch": git_branch(root),
        "logical_capacity": LOGICAL_CAPACITY,
        "logical_capacity_expression": "20^20",
        "execution_policy": "bounded-workers+queue+backpressure",
        "workers": workers,
        "preserve_existing_structure": True,
        "no_fake_implementation": True,
        "checks": checks,
        "status": "BLOCKED" if failures else "READY",
        "blocking_items": failures,
        "next_steps": [
            "inventory real files and contracts",
            "validate browser-use connector imports before smoke",
            "run API and chat E2E only after preflight",
            "build/run and collect evidence",
            "if failed: root-cause -> patch -> regenerate -> rerun",
            "final runtime gate: type text -> press สนทนา AI -> receive AI response",
        ],
    }
    out = root / args.output
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
