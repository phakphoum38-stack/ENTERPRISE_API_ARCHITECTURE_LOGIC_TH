#!/usr/bin/env python3
"""Validate the single Research OS Platform phases 1-12 certification contract."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_COMPLETE_1_12_CONTRACT.json"
GATE = ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"

REQUIRED_AUTHORITIES = {
    1: "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
    2: "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json",
    3: "current/RESEARCH_OS_PLATFORM_CORE_COMPLETION_CONTRACT.json",
    4: "current/RESEARCH_OS_UNIVERSAL_RUNNER_CONTRACT.json",
    5: "current/NATIVE_CONTROL_CENTER_OPERATING_CONTRACT.json",
    6: "current/RESEARCH_OS_100_PROJECT_READINESS_CONTRACT.json",
    7: "current/RESEARCH_OS_OWNER_EXPERIENCE_PLATFORM_CONTRACT.json",
    8: "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json",
    9: "current/RESEARCH_OS_PHASE_D_CROSS_SURFACE_PARITY_CONTRACT.json",
    10: "current/RESEARCH_OS_PHASE_E_UNIFIED_WINDOWS_DISTRIBUTION_CONTRACT.json",
    11: "current/RESEARCH_OS_PLATFORM_PRODUCTION_HARDENING_CONTRACT.json",
    12: "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
}

def fail(message: str) -> None:
    print("PLATFORM_COMPLETE_1_12=FAIL: " + message)
    raise SystemExit(1)

def main() -> None:
    if not CONTRACT.is_file():
        fail("completion contract missing")
    if not GATE.is_file():
        fail("Unified Final Gate missing")
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    phases = data.get("phases", [])
    if {p.get("phase") for p in phases} != set(REQUIRED_AUTHORITIES):
        fail("phase set must be exactly 1..12")
    for phase in phases:
        number = phase.get("phase")
        if phase.get("authority") != REQUIRED_AUTHORITIES.get(number):
            fail(f"phase {number} authority drifted")
        authority = ROOT / phase["authority"]
        if not authority.is_file():
            fail(f"phase {number} authority missing: {phase['authority']}")
    inv = data.get("required_invariants", {})
    for key in (
        "shared_execution_plane", "shared_evidence_plane",
        "no_per_project_runtime", "no_per_project_queue",
        "no_per_project_evidence_ledger",
        "owner_is_unbounded_privilege_boundary",
        "resource_conflict_is_reject_and_release",
        "same_version_overwrite_forbidden",
        "alternate_version_branching_preserved",
        "m2_is_descriptive_only",
        "final_gate_is_single_release_authority",
        "unknown_is_not_pass", "deferred_is_not_done",
    ):
        if inv.get(key) is not True:
            fail(f"required invariant missing: {key}")
    gate = GATE.read_text(encoding="utf-8")
    for marker in (
        "release_authority: final_gate",
        "release_blocked_by_unresolved_deferred: true",
        "platform_surface:",
        "m2_audit:",
        "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_COMPLETE_1_12_CONTRACT.json",
    ):
        if marker not in gate:
            fail(f"Unified Final Gate binding missing: {marker}")
    if data.get("completion_rule") != "Every phase must resolve to PASS through its canonical authority and required proof. UNKNOWN, SKIPPED, BLOCKED, STALE, CONFLICT, or unresolved DEFERRED is not certification.":
        fail("completion rule drifted")
    print("PLATFORM_COMPLETE_1_12=PASS")
    print("PHASES=1..12")
    print("SHARED_EXECUTION_PLANE=REQUIRED")
    print("SHARED_EVIDENCE_PLANE=REQUIRED")
    print("OWNER_PRIVILEGE_BOUNDARY=UNBOUNDED")
    print("RESOURCE_CONFLICT=REJECT_AND_RELEASE")
    print("FINAL_GATE=SOLE_RELEASE_AUTHORITY")

if __name__ == "__main__":
    main()
