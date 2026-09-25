#!/usr/bin/env python3
"""Validate the single system-qualification contract against existing authorities."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_SYSTEM_QUALIFICATION_CONTRACT.json"
REQUIRED_FILES = (
    "current/RESEARCH_OS_SYSTEM_QUALIFICATION_CONTRACT.json",
    "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
    "current/RESEARCH_OS_M2_AUDIT_INDEX_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_COMPLETE_1_12_CONTRACT.json",
    "current/RESEARCH_OS_100_PROJECT_READINESS_CONTRACT.json",
    "current/RESEARCH_OS_UNIVERSAL_RUNNER_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_PRODUCTION_HARDENING_CONTRACT.json",
    "current/RESEARCH_OS_PHASE_D_CROSS_SURFACE_PARITY_CONTRACT.json",
    "current/RESEARCH_OS_PHASE_E_UNIFIED_WINDOWS_DISTRIBUTION_CONTRACT.json",
    "current/AEOS_ASSURANCE_OF_ASSURANCE_CONTRACT.json",
    "tools/research_os_m2_audit.py",
    "tools/validate_aeos_final_gate_binding.py",
)
def fail(message: str) -> None:
    raise SystemExit(f"SYSTEM_QUALIFICATION=FAIL: {message}")
def main() -> None:
    if not CONTRACT.is_file():
        fail("qualification contract missing")
    try:
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid qualification contract JSON: {exc}")
    if contract.get("contract_id") != "research-os-system-qualification-v1":
        fail("unexpected contract id")
    if contract.get("status") != "ACTIVE":
        fail("qualification contract is not ACTIVE")
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("missing required authority/evidence anchors: " + ", ".join(missing))
    required_properties = (
        "exact_sha_binding","requirements_traceable_to_evidence","shared_execution_plane",
        "shared_evidence_plane","no_per_project_runtime","no_per_project_queue",
        "no_per_project_evidence_ledger","resource_conflict_is_reject_stop_release_reconcile",
        "same_version_overwrite_forbidden","alternate_version_branching_preserved",
        "owner_is_unbounded_privilege_boundary","platform_specific_navigation_forbidden",
        "m2_is_descriptive_only","aeos_is_assurance_only","final_gate_is_single_release_authority",
        "unknown_is_not_pass","deferred_is_not_done",
    )
    properties = contract.get("required_properties", {})
    if any(properties.get(key) is not True for key in required_properties):
        fail("required system properties are incomplete")
    authority = contract.get("authority", {})
    if authority.get("release_authority") != "FINAL_GATE":
        fail("qualification contract must bind release authority to FINAL_GATE")
    if authority.get("qualification_contract_is_not_release_authority") is not True:
        fail("qualification contract must not become release authority")
    gate = (ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml").read_text(encoding="utf-8")
    if "  - current/RESEARCH_OS_SYSTEM_QUALIFICATION_CONTRACT.json" not in gate:
        fail("system qualification contract is not bound to Unified Final Gate")
    print("SYSTEM_QUALIFICATION=PASS")
if __name__ == "__main__":
    main()
