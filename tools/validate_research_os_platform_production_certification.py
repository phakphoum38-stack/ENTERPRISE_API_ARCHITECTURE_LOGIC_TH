#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_PRODUCTION_CERTIFICATION_CONTRACT.json"

REQUIRED = [
    "current/RESEARCH_OS_PLATFORM_PRODUCTION_CERTIFICATION_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_RUNTIME_COMPLETION_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_RECON_REPAIR_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_FAILURE_SIMULATION_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_OBSERVABILITY_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_AI_CODE_WRITER_CONTRACT.json",
    "tools/validate_research_os_platform_runtime_completion.py",
    "tools/validate_research_os_laravel_platform.py",
    "tools/platform_spine.py",
    "tools/platform_self_reconciliation.py",
    "apps/research_os_laravel/README.md",
    "tools/validate_research_os_api_management_platform.py",
    "tools/research_os_api/api_platform/management_service.py",
    "tools/research_os_api/api_platform/management_http.py",
    "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart",
    "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
]

REQUIRED_SURFACES = {
    "platform",
    "laravel",
    "api_management",
    "recon_repair",
    "ai_code_writer",
    "workflow_queue_runner",
    "failure_recovery",
    "observability",
    "windows",
    "web",
    "ios",
}

REQUIRED_INVARIANTS = {
    "identity_capability_policy_authorization_entitlement_execution_evidence",
    "engine_event_queue_stateless_worker",
    "resource_conflict_reject_and_release",
    "unknown_not_pass",
    "main_direct_write_forbidden",
}

REQUIRED_EVIDENCE = {
    "validation",
    "tests",
    "builds",
    "runtime_smoke",
    "lineage",
    "provenance",
}


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=ROOT, text=True, capture_output=True)


def validate_contract_semantics(contract: dict) -> list[str]:
    failures: list[str] = []
    authority = contract.get("authority", {})
    for key in ("may_execute", "may_authorize", "may_approve", "may_merge", "may_release"):
        if authority.get(key) is not False:
            failures.append(f"authority_{key}_must_be_false")
    if authority.get("release_authority") != "FINAL_GATE":
        failures.append("release_authority_must_be_final_gate")

    if set(contract.get("required_surfaces", [])) != REQUIRED_SURFACES:
        failures.append("required_surfaces_drift")
    if set(contract.get("required_invariants", [])) != REQUIRED_INVARIANTS:
        failures.append("required_invariants_drift")
    if set(contract.get("evidence", [])) != REQUIRED_EVIDENCE:
        failures.append("evidence_requirements_drift")
    if contract.get("deferred_is_not_pass") is not True:
        failures.append("deferred_is_not_pass_must_be_true")
    if contract.get("release_authority") != "FINAL_GATE":
        failures.append("top_level_release_authority_must_be_final_gate")
    return failures


def main() -> int:
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    if missing:
        print("PRODUCTION_CERTIFICATION=STOP")
        print("MISSING=" + ",".join(missing))
        return 1

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    semantic_failures = validate_contract_semantics(contract)
    if semantic_failures:
        print("PRODUCTION_CERTIFICATION=STOP")
        print("CONTRACT=" + ",".join(semantic_failures))
        return 1

    checks = [
        ["tools/validate_research_os_platform_runtime_completion.py"],
        ["tools/validate_research_os_laravel_platform.py"],
        ["tools/platform_spine.py", "--validate"],
        ["tools/validate_platform_self_reconciliation.py"],
        ["tools/validate_research_os_api_management_platform.py"],
    ]
    for cmd in checks:
        result = run(*cmd)
        if result.returncode:
            print("PRODUCTION_CERTIFICATION=STOP")
            print((result.stdout or result.stderr)[-4000:])
            return 1

    print("PRODUCTION_CERTIFICATION=PASS")
    print("PLATFORM_RUNTIME=QUALIFIED")
    print("API_MANAGEMENT=QUALIFIED")
    print("RECON_REPAIR=BOUNDED")
    print("FAILURE_RECOVERY=QUALIFIED")
    print("OBSERVABILITY=QUALIFIED")
    print("AI_CODE_WRITER=RECON_BOUND")
    print("SURFACES=11_REQUIRED")
    print("INVARIANTS=5_REQUIRED")
    print("EVIDENCE=6_REQUIRED")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
