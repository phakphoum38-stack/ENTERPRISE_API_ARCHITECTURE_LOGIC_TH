#!/usr/bin/env python3
"""Validate the canonical Platform Evolution contract against existing Platform authorities."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_EVOLUTION_CONTRACT.json"
REGISTRY = ROOT / "current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json"
SCHEMA = ROOT / "current/RESEARCH_OS_PLATFORM_COMPONENT_REGISTRY_SCHEMA.json"
GOVERNANCE = ROOT / "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json"
SPINE_CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_SPINE_ENGINE_CONTRACT.json"
FINAL_GATE = ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"

def fail(message: str) -> None:
    print("PLATFORM_EVOLUTION=FAIL: " + message)
    raise SystemExit(1)

def main() -> int:
    for path in (CONTRACT, REGISTRY, SCHEMA, GOVERNANCE, SPINE_CONTRACT, FINAL_GATE):
        if not path.is_file():
            fail("missing canonical source: " + str(path.relative_to(ROOT)))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    governance = json.loads(GOVERNANCE.read_text(encoding="utf-8"))
    spine_contract = json.loads(SPINE_CONTRACT.read_text(encoding="utf-8"))
    gate = FINAL_GATE.read_text(encoding="utf-8")

    if contract.get("status") != "ACTIVE":
        fail("evolution contract is not ACTIVE")
    authority = contract.get("authority", {})
    if any(authority.get(k) is not False for k in ("may_execute","may_authorize","may_approve","may_merge","may_release")):
        fail("evolution layer acquired authority")
    if authority.get("release_authority") != "FINAL_GATE":
        fail("release authority drifted")

    evolution = contract.get("evolution", {})
    compatibility = evolution.get("compatibility", {})
    if compatibility.get("unknown") != "HOLD":
        fail("unknown compatibility is not HOLD")
    if compatibility.get("breaking_requires") != ["PLAN","COMPATIBILITY","MIGRATE","VALIDATE","EVIDENCE","RETIRE_OLD"]:
        fail("breaking migration sequence drifted")
    if compatibility.get("rollback_required") is not True:
        fail("breaking migration rollback is not required")
    lifecycle = evolution.get("lifecycle", {})
    expected_states = ["PROPOSED","EXPERIMENTAL","ACTIVE","DEPRECATED","RETIRED"]
    if lifecycle.get("states") != expected_states or lifecycle.get("backward_transition") != "FORBIDDEN":
        fail("lifecycle model drifted")
    impact = evolution.get("impact", {})
    if set(impact.get("required_categories", [])) != {"contracts","workflows","tests","final_gate","invariants","product_surfaces"}:
        fail("impact categories incomplete")
    if impact.get("unknown") != "HOLD" or impact.get("high_impact_threshold") != "CROSS_PROJECT":
        fail("impact fail-closed policy drifted")
    simulation = evolution.get("simulation", {})
    if simulation.get("required_for") != "CROSS_PROJECT" or simulation.get("checks") != ["dependency","impact","contract","failure","rollback"]:
        fail("simulation contract incomplete")
    reconciliation = evolution.get("reconciliation", {})
    if reconciliation.get("ambiguous_target") != "STOP" or reconciliation.get("protected_core") != "STOP":
        fail("repair boundary drifted")
    ai = evolution.get("ai_code_writer", {})
    if not ai.get("must_not_invent_canonical_authority"):
        fail("AI authority boundary missing")
    cert = contract.get("certification", {})
    if cert.get("unknown_is_not_pass") is not True or cert.get("release_authority_remains") != "FINAL_GATE":
        fail("certification fail-closed policy drifted")

    schema_count = schema.get("properties", {}).get("count_is_informational", {}).get("const")
    if schema.get("schema_version") != 1 or schema_count is not True or registry.get("count_is_informational") is not True:
        fail("schema-driven registry contract drifted")
    components = registry.get("components", [])
    ids = {c.get("id") for c in components}
    if len(ids) != len(components) or not ids:
        fail("component registry identity invalid")
    required = [c for c in components if c.get("required") is True]
    if any(c.get("lifecycle") != "ACTIVE" for c in required):
        fail("required component is not ACTIVE")
    if governance.get("authority", {}).get("release_authority") != "FINAL_GATE":
        fail("governance release authority drifted")
    if spine_contract.get("authority", {}).get("release_authority") != "FINAL_GATE":
        fail("spine release authority drifted")

    required_gate_anchors = (
        "release_authority: final_gate",
        "current/RESEARCH_OS_PLATFORM_COMPONENT_REGISTRY_SCHEMA.json",
        "current/RESEARCH_OS_PLATFORM_SPINE_ENGINE_CONTRACT.json",
        "platform_spine_engine:",
        "self_reconciliation:",
    )
    for anchor in required_gate_anchors:
        if anchor not in gate:
            fail("Final Gate anchor missing: " + anchor)

    spine = subprocess.run([sys.executable, "tools/platform_spine.py", "--validate"], cwd=ROOT, text=True, capture_output=True)
    if spine.returncode != 0:
        fail("Platform Spine validation failed: " + (spine.stdout or spine.stderr).strip())
    recon = subprocess.run([sys.executable, "tools/validate_platform_self_reconciliation.py"], cwd=ROOT, text=True, capture_output=True)
    if recon.returncode != 0:
        fail("Platform reconciliation validation failed: " + (recon.stdout or recon.stderr).strip())

    print("PLATFORM_EVOLUTION=PASS")
    print("PLATFORM_CONTRACT_EVOLUTION=BOUND")
    print("PLATFORM_OWNERSHIP=METADATA_ONLY")
    print("PLATFORM_IMPACT=FAIL_CLOSED")
    print("PLATFORM_SIMULATION=CROSS_PROJECT_REQUIRED")
    print("PLATFORM_RECONCILIATION=BOUNDED")
    print("PLATFORM_AI_CODE_WRITER=RECON_BOUND")
    print("PLATFORM_CERTIFICATION=FINAL_GATE")
    print("PLATFORM_RELEASE_AUTHORITY=FINAL_GATE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
