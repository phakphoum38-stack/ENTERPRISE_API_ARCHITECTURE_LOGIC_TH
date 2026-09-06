#!/usr/bin/env python3
"""Safety gate for generated workflow repair plans."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "GOLDEN_RELEASE_CONTRACT.yml"
PROTECTED = {"TARGET_SHA", "OWNER_BUILD_IDENTITY", "SHA256", "INSTALLED_PROVENANCE", "CANONICAL_LINEAGE", "RELEASE_CERTIFICATION"}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--plan", default=str(ROOT / "reports" / "WORKFLOW_REPAIR_PLAN.json"))
    args = p.parse_args()
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    errors: list[str] = []
    if plan.get("auto_apply_to_main") is not False:
        errors.append("auto-apply-to-main must remain false")
    if plan.get("auto_merge") is not False:
        errors.append("auto-merge must remain false")
    if plan.get("status") == "REPAIR_PLAN_READY" and plan.get("protected_gate_changes"):
        errors.append("protected gate changes require human approval")
    if set(plan.get("protected_gate_changes", []) if isinstance(plan.get("protected_gate_changes"), list) else []) & PROTECTED:
        errors.append("repair explicitly touches a protected gate")
    if not CONTRACT.exists():
        errors.append("golden release contract missing")
    result = {"version": 1, "status": "PASS" if not errors else "FAIL", "errors": errors}
    (ROOT / "reports" / "WORKFLOW_REPAIR_VALIDATION.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
