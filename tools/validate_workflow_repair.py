#!/usr/bin/env python3
"""Safety gate for generated workflow repair plans."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "GOLDEN_RELEASE_CONTRACT.yml"
PROTECTED = {"TARGET_SHA", "OWNER_BUILD_IDENTITY", "SHA256", "INSTALLED_PROVENANCE", "CANONICAL_LINEAGE", "RELEASE_CERTIFICATION"}
FORBIDDEN = {"github.sha", "GITHUB_SHA", "auto-merge", "delete provenance", "disable identity", "skip certification"}


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
    changes = plan.get("changes", [])
    if not isinstance(changes, list):
        errors.append("changes must be a list")
        changes = []
    if len(changes) > 250:
        errors.append("repair exceeds maximum 250 change entries")
    protected_changes = plan.get("protected_gate_changes", [])
    if protected_changes not in (False, None) and not isinstance(protected_changes, list):
        errors.append("protected_gate_changes must be false or a list")
    if isinstance(protected_changes, list) and set(protected_changes) & PROTECTED:
        errors.append("repair explicitly touches a protected gate")
    serialized = json.dumps(plan, sort_keys=True).lower()
    for forbidden in FORBIDDEN:
        if forbidden.lower() in serialized:
            errors.append(f"forbidden repair instruction detected: {forbidden}")
    if not CONTRACT.exists():
        errors.append("golden release contract missing")
    else:
        contract = CONTRACT.read_text(encoding="utf-8")
        required = ["auto_apply_to_main: false", "auto_merge: false", "protected_gate_changes_require_human_approval: true", "required_before_release: true"]
        for marker in required:
            if marker not in contract:
                errors.append(f"golden contract missing safety rule: {marker}")
    result = {"version": 2, "status": "PASS" if not errors else "FAIL", "errors": errors}
    out = ROOT / "reports" / "WORKFLOW_REPAIR_VALIDATION.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
