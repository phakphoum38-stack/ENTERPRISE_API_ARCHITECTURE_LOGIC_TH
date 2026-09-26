#!/usr/bin/env python3
"""Validation-only production completion reconciliation over existing authorities."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "current/ARCHITECTURE_COMPLETENESS_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json",
    "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
    "tools/validate_research_os_unified_final_gate.py",
    "tools/platform_graph.py",
    "current/RESEARCH_OS_MEMORY_FABRIC_CONTRACT.json",
    "current/RESEARCH_OS_UNIVERSAL_RUNNER_CONTRACT.json",
    "current/RESEARCH_OS_RUNNER_INSTALLATION_CONTRACT.json",
    "current/RESEARCH_OS_PHASE_E_UNIFIED_WINDOWS_DISTRIBUTION_CONTRACT.json",
    "packages/research_os_contracts/lib/migration_contract.dart",
    "current/AEOS_ASSURANCE_OF_ASSURANCE_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_RUNTIME_READINESS_CONTRACT.json",
    "current/PLATFORM_OPERATIONALIZATION_CONTRACT.json",
    "tools/platform_operationalization.py",
    "tools/test_platform_operationalization.py",
    "tools/validate_platform_operationalization.py",
    "tools/platform_runtime_readiness.py",
    "tools/test_platform_runtime_readiness.py",
)

def validate_production_completion() -> tuple[str, ...]:
    failures: list[str] = []
    contract_path = ROOT / "current/RESEARCH_OS_PLATFORM_PRODUCTION_COMPLETION_CONTRACT.json"
    if not contract_path.is_file():
        return ("missing_completion_contract",)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    if contract.get("status") != "ACTIVE":
        failures.append("completion_contract_not_active")
    if contract.get("required_proofs", {}).get("runtime_readiness_state_machine") is not True:
        failures.append("runtime_readiness_proof_missing")
    failures.extend(f"missing:{p}" for p in REQUIRED if not (ROOT / p).is_file())
    gate = (ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml").read_text(encoding="utf-8")
    validator = (ROOT / "tools/validate_research_os_unified_final_gate.py").read_text(encoding="utf-8")
    governance = json.loads((ROOT / "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json").read_text(encoding="utf-8"))
    completeness = json.loads((ROOT / "current/ARCHITECTURE_COMPLETENESS_CONTRACT.json").read_text(encoding="utf-8"))
    if "release_authority: final_gate" not in gate:
        failures.append("final_gate_authority_missing")
    if "unknown_gate_state: STOP" not in gate:
        failures.append("unknown_gate_not_fail_closed")
    if "deferred_is_not_pass: true" not in gate:
        failures.append("deferred_policy_missing")
    if "RESEARCH_OS_PLATFORM_PRODUCTION_COMPLETION_CONTRACT.json" not in gate:
        failures.append("completion_contract_not_bound_to_final_gate")
    if "RESEARCH_OS_PLATFORM_PRODUCTION_COMPLETION_CONTRACT.json" not in validator:
        failures.append("completion_contract_not_bound_to_validator")
    if "runtime_readiness:" not in gate or "RESEARCH_OS_PLATFORM_RUNTIME_READINESS_CONTRACT.json" not in gate:
        failures.append("runtime_readiness_not_bound_to_final_gate")
    readiness = json.loads((ROOT / "current/RESEARCH_OS_PLATFORM_RUNTIME_READINESS_CONTRACT.json").read_text(encoding="utf-8"))
    if readiness.get("authority", {}).get("release_authority") != "FINAL_GATE":
        failures.append("runtime_readiness_release_authority_drift")
    if readiness.get("authority", {}).get("may_execute") is not False:
        failures.append("runtime_readiness_may_not_execute")
    if readiness.get("rules", {}).get("evidence_is_projection_only") is not True:
        failures.append("runtime_readiness_evidence_authority_drift")
    if governance.get("authority", {}).get("release_authority") != "FINAL_GATE":
        failures.append("governance_release_authority_drift")
    if completeness.get("verification_policy", {}).get("unknown_policy") != "FAIL":
        failures.append("completeness_unknown_policy_drift")
    graph = (ROOT / "tools/platform_graph.py").read_text(encoding="utf-8")
    if "descriptive/read-only" not in graph:
        failures.append("platform_graph_authority_boundary_missing")
    migration = (ROOT / "packages/research_os_contracts/lib/migration_contract.dart").read_text(encoding="utf-8")
    for marker in ("preflight", "migrate", "rollback", "postflight"):
        if marker not in migration:
            failures.append(f"migration_contract_missing:{marker}")
    assurance = json.loads((ROOT / "current/AEOS_ASSURANCE_OF_ASSURANCE_CONTRACT.json").read_text(encoding="utf-8"))
    inputs = set(assurance.get("required_inputs", []))
    for field in ("target_sha", "contract_sha", "evidence_root"):
        if field not in inputs:
            failures.append(f"assurance_input_missing:{field}")
    return tuple(failures)

def run_production_completion() -> dict[str, str]:
    failures = validate_production_completion()
    return {"status": "PASS" if not failures else "FAIL", "failure_count": str(len(failures)), "release_authority": "FINAL_GATE"}

if __name__ == "__main__":
    errors = validate_production_completion()
    if errors:
        print("PLATFORM_PRODUCTION_COMPLETION=FAIL")
        print("\n".join(errors))
        raise SystemExit(1)
    print("PLATFORM_PRODUCTION_COMPLETION=PASS")
    print("RELEASE_AUTHORITY=FINAL_GATE")
