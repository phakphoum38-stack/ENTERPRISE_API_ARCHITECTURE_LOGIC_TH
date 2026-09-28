#!/usr/bin/env python3
"""Fail-closed validator for the native Experience Studio contract."""
from __future__ import annotations

import json
from pathlib import Path


REQUIRED = {
    "contract_id",
    "version",
    "root_ref",
    "control_plane_ref",
    "states",
    "required_capabilities",
    "required_component_states",
    "motion_rules",
    "evidence_requirements",
    "forbidden",
    "invariants",
}


def validate(path: str | Path = "current/EXPERIENCE_NATIVE_DESIGN_STUDIO_CONTRACT.json") -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - set(payload))
    if missing:
        raise ValueError(f"missing_contract_fields:{','.join(missing)}")
    if payload["authority"] != "descriptive_only":
        raise ValueError("authority_must_remain_descriptive_only")
    if payload["logical_coverage"] != "10^1000" or payload["materialization"] != "bounded_only":
        raise ValueError("invalid_coverage_boundary")
    if "reduced_motion_supported" not in payload["motion_rules"]:
        raise ValueError("reduced_motion_requirement_missing")
    forbidden = set(payload["forbidden"])
    if {"merge_authority", "authority_mutation"} - forbidden:
        raise ValueError("authority_forbidden_boundary_missing")
    return {"status": "PASS", "contract_id": payload["contract_id"], "version": payload["version"]}


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
