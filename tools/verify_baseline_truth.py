#!/usr/bin/env python3
"""Machine-verifies the immutable P0-01 baseline truth anchors."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_CONTRACT = Path("current/BASELINE_TRUTH_CONTRACT.json")


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def commit_exists(sha: str) -> bool:
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0


def verify(contract_path: Path, expected_head: str | None = None) -> int:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    production = contract["production_code_truth"]["commit"]
    canonical = contract["canonical_main_history_truth"]["commit"]
    head = expected_head or run_git("rev-parse", "HEAD")

    failures: list[str] = []
    if not commit_exists(production):
        failures.append(f"production commit missing: {production}")
    if not commit_exists(canonical):
        failures.append(f"canonical commit missing: {canonical}")

    # The current working HEAD is intentionally reported separately. It is
    # never promoted to production truth merely because it is checked out.
    report = {
        "schema_version": contract["schema_version"],
        "production_code_truth": production,
        "canonical_main_history_truth": canonical,
        "working_head": head,
        "working_head_is_production_truth": head == production,
        "working_head_is_canonical_history_anchor": head == canonical,
        "status": "FAIL" if failures else "PASS",
        "failures": failures,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    if failures:
        return 1
    print("BASELINE_TRUTH_GATE=PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--head", help="Explicit working HEAD SHA for deterministic CI checks")
    parser.add_argument("--contract", type=Path, default=DEFAULT_CONTRACT)
    args = parser.parse_args()
    if not args.contract.is_file():
        print(f"BASELINE_TRUTH_GATE=FAIL: missing {args.contract}")
        return 1
    try:
        return verify(args.contract, args.head)
    except (OSError, RuntimeError, json.JSONDecodeError, KeyError) as exc:
        print(f"BASELINE_TRUTH_GATE=FAIL: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
