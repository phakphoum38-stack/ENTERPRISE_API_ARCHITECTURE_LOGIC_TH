#!/usr/bin/env python3
"""Safe command dispatcher for Research OS workflows.

Only commands declared in COMMANDS are executable. Arbitrary shell input is rejected.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from house_brain import analyze

ROOT = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT / "artifacts" / "house-command"

COMMANDS: dict[str, list[list[str]]] = {
    "validate": [
        [sys.executable, "tools/research_curator/curator.py", "validate", "--output", "research/artifacts"],
    ],
    "test": [
        [sys.executable, "-m", "unittest", "discover", "-s", "tools/research_curator", "-p", "test_*.py", "-v"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tools/research_os_api", "-p", "test_*.py", "-v"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tools/house_command", "-p", "test_*.py", "-v"],
    ],
    "graph": [
        [sys.executable, "tools/research_curator/knowledge_ops.py", "graph", "--artifacts", "research/artifacts", "--output", "artifacts/house-command/knowledge-graph"],
    ],
    "house-status": [],
    "all": [],
}


def run_process(command: Sequence[str]) -> dict[str, object]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "command": list(command),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def build_house_status() -> dict[str, object]:
    status = analyze(ROOT)
    return {"ok": not status["missing"], "status": status}


def execute(command_name: str) -> dict[str, object]:
    if command_name not in COMMANDS:
        raise ValueError(f"Unsupported command: {command_name}")

    requested = ["validate", "test", "graph", "house-status"] if command_name == "all" else [command_name]
    results: list[dict[str, object]] = []
    ok = True

    for item in requested:
        if item == "house-status":
            status = build_house_status()
            results.append({"name": item, **status})
            ok = ok and bool(status["ok"])
            continue

        process_results = [run_process(cmd) for cmd in COMMANDS[item]]
        item_ok = all(int(result["returncode"]) == 0 for result in process_results)
        results.append({"name": item, "ok": item_ok, "steps": process_results})
        ok = ok and item_ok

    return {
        "schema_version": "1.1",
        "command": command_name,
        "ok": ok,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an allowlisted Research OS house command")
    parser.add_argument("command", choices=sorted(COMMANDS))
    parser.add_argument("--report", default=str(REPORT_DIR / "report.json"))
    args = parser.parse_args()

    report_path = ROOT / args.report if not Path(args.report).is_absolute() else Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = execute(args.command)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
