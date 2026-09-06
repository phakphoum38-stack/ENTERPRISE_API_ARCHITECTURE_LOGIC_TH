#!/usr/bin/env python3
"""Generate a bounded repair plan; never edits protected gates or main directly."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

SAFE_RULES = {
    "STALE_LASTEXITCODE": {
        "description": "Reset LASTEXITCODE explicitly after successful PowerShell verifier invocation before testing it.",
        "validation": ["PowerShell script returns success", "provenance evidence remains unchanged", "workflow YAML validates"],
    },
    "TRANSIENT_NETWORK": {
        "description": "Use bounded retry only around the identified transient operation; do not retry release/provenance mismatches.",
        "validation": ["retry count bounded", "protected gates unchanged", "workflow YAML validates"],
    },
    "YAML_FAILURE": {
        "description": "Repair YAML syntax only; preserve jobs, needs, TARGET_SHA and protected gates.",
        "validation": ["yaml parse succeeds", "dependency graph unchanged except intended syntax fix"],
    },
}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--analysis", default=str(REPORTS / "WORKFLOW_FAILURE_ANALYSIS.json"))
    p.add_argument("--workflow", default="unknown")
    args = p.parse_args()
    analysis = json.loads(Path(args.analysis).read_text(encoding="utf-8"))
    code = analysis.get("classification", "UNKNOWN_FAILURE")
    rule = SAFE_RULES.get(code)
    if not rule or analysis.get("status") == "HUMAN_APPROVAL_REQUIRED":
        plan = {
            "version": 1,
            "status": "BLOCKED",
            "reason": "No safe allowlisted repair exists or a protected gate is involved.",
            "workflow": args.workflow,
            "classification": code,
            "changes": [],
            "auto_apply_to_main": False,
            "auto_merge": False,
        }
    else:
        plan = {
            "version": 1,
            "status": "REPAIR_PLAN_READY",
            "workflow": args.workflow,
            "classification": code,
            "description": rule["description"],
            "validation": rule["validation"],
            "changes": [],
            "requires_pr": True,
            "auto_apply_to_main": False,
            "auto_merge": False,
            "protected_gate_changes": False,
        }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "WORKFLOW_REPAIR_PLAN.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
