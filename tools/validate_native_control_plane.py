#!/usr/bin/env python3
"""Fail-closed validator for the native control-plane contract."""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "NATIVE_CONTROL_PLANE_CONTRACT.json"
ENGINE = ROOT / "tools" / "native_control_plane.py"

REQUIRED_ENGINES = {"control", "experience", "knowledge", "assurance"}
REQUIRED_INVARIANTS = {
    "one_control_plane",
    "one_command_model",
    "one_object_inspector_model",
    "unknown_is_not_known",
    "confidence_is_not_truth",
    "assurance_is_not_authority",
    "evidence_precedes_confidence",
    "history_is_preserved",
    "recovery_is_explicit",
    "10^1000_is_logical_only",
    "no_automatic_merge",
    "no_automatic_authority_grant",
}


def validate() -> list[str]:
    errors: list[str] = []
    if not CONTRACT.is_file():
        return ["missing contract"]
    if not ENGINE.is_file():
        errors.append("missing engine")
    try:
        data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"invalid contract JSON: {exc}"]

    if data.get("contract_id") != "research-os-native-control-plane-v1":
        errors.append("invalid contract identity")
    engines = {item.get("id") for item in data.get("engines", [])}
    if engines != REQUIRED_ENGINES:
        errors.append(f"engine set mismatch: {sorted(engines)}")
    if set(data.get("invariants", [])) != REQUIRED_INVARIANTS:
        errors.append("invariant set mismatch")
    if data.get("motion", {}).get("reduced_motion_supported") is not True:
        errors.append("reduced-motion support is required")
    human = data.get("human_control", {})
    if "APPROVE" not in human.get("human_required", []):
        errors.append("human approval boundary missing")
    if "RELEASE" not in human.get("human_required", []):
        errors.append("human release boundary missing")
    if data.get("bounds", {}).get("commands_per_dispatch", 0) <= 0:
        errors.append("command bound must be positive")
    return errors


if __name__ == "__main__":
    problems = validate()
    if problems:
        print("NATIVE_CONTROL_PLANE_GATE=FAIL")
        for problem in problems:
            print(problem)
        sys.exit(1)
    print("NATIVE_CONTROL_PLANE_GATE=PASS")
