#!/usr/bin/env python3
"""Validate the Research OS Flutter convergence map without deleting or rewriting roots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_FLUTTER_CONVERGENCE_MAP.json"
ALLOWED = {"canonical", "migrate", "adapter", "platform-only", "retire"}
REQUIRED_ROOTS = {
    "owner_special/flutter_app",
    "apps/research_os_flutter",
    "v3/flutter_app",
}


def load() -> dict[str, Any]:
    with CONTRACT.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if data.get("contract") != "research-os-flutter-convergence-map":
        errors.append("unexpected contract id")
    if data.get("retirement_policy") != "NO_DELETE_UNTIL_PARITY_AND_ALL_APPLICABLE_GATES_PASS":
        errors.append("retirement policy is not fail-closed")
    if set(data.get("classifications", [])) != ALLOWED:
        errors.append("classification vocabulary drift")
    roots = data.get("roots", [])
    root_names = {r.get("root") for r in roots}
    missing = REQUIRED_ROOTS - root_names
    if missing:
        errors.append(f"missing roots: {sorted(missing)}")
    if len(root_names) != len(roots):
        errors.append("duplicate root entries")
    for root in roots:
        if root.get("retire") is True:
            errors.append(f"retire=true is forbidden in planning map: {root.get('root')}")
        for feature in root.get("features", []):
            if feature.get("classification") not in ALLOWED:
                errors.append(f"invalid classification: {root.get('root')}:{feature.get('path')}")
            if not feature.get("path") or not feature.get("capability"):
                errors.append(f"incomplete feature entry: {root.get('root')}")
    if not data.get("shared_contracts"):
        errors.append("shared_contracts must not be empty")
    if not data.get("forbidden_convergence_actions"):
        errors.append("forbidden_convergence_actions must not be empty")
    return errors


def main() -> int:
    errors = validate(load())
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] Research OS Flutter convergence map is structurally valid")
    print("[PASS] Three Flutter roots are explicitly classified")
    print("[PASS] Retirement remains fail-closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
