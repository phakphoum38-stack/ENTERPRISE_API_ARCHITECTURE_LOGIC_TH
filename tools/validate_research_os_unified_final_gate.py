#!/usr/bin/env python3
"""Validate the Research OS Unified Final Gate contract and its source anchors."""
from __future__ import annotations
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_UNIFIED_FINAL_GATE.yml"

REQUIRED_FILES = (
    "current/CANONICAL_PLATFORM_CONTRACT.yml",
    "current/GOLDEN_RELEASE_CONTRACT.yml",
    "current/RESEARCH_OS_PHASE_B_LIFECYCLE_EVIDENCE_CONTRACT.json",
    "current/RESEARCH_OS_PHASE_C_CAPABILITY_E2E_BINDING_CONTRACT.json",
    "current/RESEARCH_OS_PHASE_D_CROSS_SURFACE_PARITY_CONTRACT.json",
    "current/RESEARCH_OS_PHASE_E_UNIFIED_WINDOWS_DISTRIBUTION_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_CORE_COMPLETION_CONTRACT.json",
    "current/RESEARCH_OS_100_PROJECT_READINESS_CONTRACT.json",
    "current/RESEARCH_OS_PROJECT_TEMPLATE_CONTRACT.json",
    "current/RESEARCH_OS_PROJECT_001.json",
    "current/RESEARCH_OS_PROJECT_LIFECYCLE_CONTRACT.json",
    "current/RESEARCH_OS_PROJECT_SCALE_EXECUTION_CONTRACT.json",
    "current/RESEARCH_OS_PROJECT_EXPERIENCE_CONTRACT.json",
    "current/RESEARCH_OS_WORKFLOW_EXPERIENCE_CONTRACT.json",
    "current/RESEARCH_OS_MAIN_FINAL_AUDIT_CONTROL_CENTER_CONTRACT.json",
    "current/RESEARCH_OS_OWNER_EXPERIENCE_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_DEFECT_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_SCHEDULE_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_RISK_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_CHANGE_IMPACT_CONTRACT.json",
    "current/RESEARCH_OS_MEMORY_FABRIC_CONTRACT.json",
    "current/RESEARCH_OS_UNIVERSAL_RUNNER_CONTRACT.json",
    "current/RESEARCH_OS_RUNNER_INSTALLATION_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_PRODUCTION_HARDENING_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_PRODUCTION_COMPLETION_CONTRACT.json",
    "current/RESEARCH_OS_OWNER_EXPERIENCE_PLATFORM_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_COMPLETION_SCHEDULE_CONTRACT.json",
    "current/RESEARCH_OS_M2_AUDIT_INDEX_CONTRACT.json",
    "current/RESEARCH_OS_M2_PLATFORM_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_SERVICE_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_RUNTIME_RESOLUTION_CONTRACT.json",
    "current/RESEARCH_OS_CAPABILITY_CONVERGENCE_CONTRACT.json",
    "current/RESEARCH_OS_AUTHORIZATION_CONVERGENCE_CONTRACT.json",
    "current/RESEARCH_OS_IDENTITY_ACCESS_WAVE_1_MAP.json",
    "tools/validate_research_os_identity_access_wave1.py",
    "tools/test_validate_research_os_identity_access_wave1.py",
    "current/PLATFORM_PROJECT_SNAPSHOT_CONTRACT.json",
    "current/PLATFORM_OPERATIONALIZATION_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_COMPLETE_1_12_CONTRACT.json",
    "current/RESEARCH_OS_SYSTEM_QUALIFICATION_CONTRACT.json",
    "tools/validate_research_os_system_qualification.py",
    "tools/test_validate_research_os_system_qualification.py",
    "tools/research_os_m2_audit.py",
    "tools/test_research_os_m2_audit.py",
    "tools/validate_platform_completion_schedule.py",
    "tools/validate_platform_service.py",
    "tools/test_platform_service.py",
    "tools/validate_platform_runtime_resolution.py",
    "tools/test_validate_platform_runtime_resolution.py",
    "tools/test_validate_platform_service.py",
    "tools/platform_operationalization.py",
    "tools/test_platform_operationalization.py",
    "tools/validate_platform_operationalization.py",
    "tools/test_platform_completion_schedule.py",
    "tools/validate_owner_experience_platform.py",
    "tools/test_owner_experience_platform.py",
    "tools/platform_production_hardening.py",
    "tools/test_platform_production_hardening.py",
    "tools/test_runner_installer.py",
    "tools/research_os_api/runner_installer.py",
    "scripts/bootstrap-research-os.py",
    "tools/test_platform_operating_control.py",
    "apps/research_os_flutter/lib/src/features/owner/owner_experience_page.dart",
    "apps/research_os_flutter/test/owner_experience_page_test.dart",
    "apps/research_os_flutter/lib/src/features/control_center/native_control_audit_view.dart",
    "apps/research_os_flutter/lib/src/features/projects/project_experience_page.dart",
    "apps/research_os_flutter/lib/src/features/workflows/workflow_experience_page.dart",
    "tools/research_os_api/test_project_routes.py",
    "apps/research_os_flutter/test/project_experience_page_test.dart",
    "apps/research_os_flutter/test/workflow_experience_page_test.dart",
    "apps/research_os_flutter/lib/src/features/control_center/native_control_center_page.dart",
    "tools/project_scale_execution.py",
    "tools/test_project_scale_execution.py",
    "tools/project_execution.py",
    "tools/test_project_execution.py",
    "tools/runtime_evidence.py",
    "tools/test_runtime_evidence.py",
    "tools/project_registry.py",
    "tools/validate_platform_governance.py",
    "current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json",
    "tools/platform_governance_report.py",
    "tools/test_project_registry.py",
    ".github/workflows/research-os-gate.yml",
    ".github/workflows/research-os-final-gate.yml",
    ".github/workflows/research-os-platform-surface-matrix.yml",
    ".github/workflows/research-os-ios-ipa.yml",
    ".github/workflows/research-os-phase-e-unified-windows-distribution.yml",
    ".github/workflows/research-os-release-spine-gate.yml",
    ".github/workflows/research-os-unified-final-gate.yml",
    ".github/workflows/owner-special-build-identity-gate.yml",
    ".github/workflows/owner-special-friend.yml",
    ".github/workflows/owner-special-ios-ipa.yml",
    "tools/aeos_master_assurance.py",
    "tools/validate_aeos_final_gate_binding.py",
    "tools/test_validate_aeos_final_gate_binding.py",
    "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart",
    "apps/research_os_flutter/test/platform_surface_parity_test.dart",
    "apps/research_os_flutter/test/desktop_shell_test.dart",
)

EXPECTED_SPINE = (
    "identity", "capability", "authorization", "navigation", "page_feature",
    "workflow", "event_queue", "stateless_runner", "evidence_provenance",
    "aeos_recheck", "final_gate", "release",
)

def fail(message: str) -> "NoReturn":
    print(f"UNIFIED_FINAL_GATE=FAIL: {message}")
    raise SystemExit(1)

def main() -> None:
    if not CONTRACT.is_file():
        fail(f"missing contract: {CONTRACT}")
    text = CONTRACT.read_text(encoding="utf-8")
    if "name: Research OS Unified Final Gate" not in text:
        fail("contract name is missing")
    if "release_authority: final_gate" not in text:
        fail("final gate is not declared as release authority")
    if "deferred_is_not_pass: true" not in text:
        fail("deferred policy is not fail-closed")
    if "release_blocked_by_unresolved_deferred: true" not in text:
        fail("unresolved deferred release policy is missing")
    required_assurance = (
        "authority: existing_aeos_master_assurance",
        "execution_boundary: tools/aeos_master_assurance.py",
        "evidence_validator: tools/validate_aeos_final_gate_binding.py",
        "evidence_schema: AEOS_MASTER_ASSURANCE_V2",
        "target_sha: exact_unified_final_gate_target_sha",
        "required_decision: PASS",
        "missing_aeos_recheck: STOP",
        "aeos_non_pass: STOP",
    )
    missing_assurance = [item for item in required_assurance if item not in text]
    if missing_assurance:
        fail("AEOS Final Gate binding is incomplete: " + ", ".join(missing_assurance))
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        fail("missing required anchors: " + ", ".join(missing))
    for contract_ref in (
        "current/RESEARCH_OS_PLATFORM_CORE_COMPLETION_CONTRACT.json",
        "current/RESEARCH_OS_100_PROJECT_READINESS_CONTRACT.json",
        "current/RESEARCH_OS_PROJECT_TEMPLATE_CONTRACT.json",
        "current/RESEARCH_OS_PROJECT_001.json",
        "current/RESEARCH_OS_PROJECT_LIFECYCLE_CONTRACT.json",
        "current/RESEARCH_OS_PROJECT_SCALE_EXECUTION_CONTRACT.json",
        "current/RESEARCH_OS_PROJECT_EXPERIENCE_CONTRACT.json",
        "current/RESEARCH_OS_WORKFLOW_EXPERIENCE_CONTRACT.json",
        "current/RESEARCH_OS_MAIN_FINAL_AUDIT_CONTROL_CENTER_CONTRACT.json",
        "current/RESEARCH_OS_OWNER_EXPERIENCE_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_DEFECT_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_SCHEDULE_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_RISK_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_CHANGE_IMPACT_CONTRACT.json",
        "current/RESEARCH_OS_MEMORY_FABRIC_CONTRACT.json",
        "current/RESEARCH_OS_UNIVERSAL_RUNNER_CONTRACT.json",
        "current/RESEARCH_OS_RUNNER_INSTALLATION_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_PRODUCTION_HARDENING_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_PRODUCTION_COMPLETION_CONTRACT.json",
        "current/RESEARCH_OS_OWNER_EXPERIENCE_PLATFORM_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_COMPLETION_SCHEDULE_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json",
        "current/RESEARCH_OS_M2_PLATFORM_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_SERVICE_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_RUNTIME_RESOLUTION_CONTRACT.json",
        "current/RESEARCH_OS_CAPABILITY_CONVERGENCE_CONTRACT.json",
        "current/PLATFORM_PROJECT_SNAPSHOT_CONTRACT.json",
        "current/PLATFORM_OPERATIONALIZATION_CONTRACT.json",
        "current/RESEARCH_OS_SYSTEM_QUALIFICATION_CONTRACT.json",
    ):
        if f"  - {contract_ref}" not in text:
            fail(f"required completion contract is not bound: {contract_ref}")
    navigation = (ROOT / "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart").read_text(encoding="utf-8")
    marker = "const researchNavigationItems"
    if marker not in navigation:
        fail("navigation registry declaration is missing")
    registry = navigation.split(marker, 1)[1].split("];", 1)[0]
    entries = re.findall(r"ResearchNavItem\((.*?)\),\s*(?=ResearchNavItem|$)", registry, flags=re.DOTALL)
    indexes: list[int] = []
    for entry in entries:
        index_match = re.search(r",\s*(\d+)\s*,\s*(?:required:|destinationId:|capabilityId:|\})", entry)
        if index_match is None:
            index_match = re.search(r",\s*(\d+)\s*,", entry)
        if index_match is None:
            fail("navigation entry is missing a stable index")
        indexes.append(int(index_match.group(1)))
    if not indexes:
        fail("navigation registry is empty")
    if sorted(indexes) != list(range(len(indexes))):
        fail(f"navigation indexes drifted: {indexes}")
    identity_access = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_research_os_identity_access_wave1.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if identity_access.returncode != 0:
        fail(
            "Identity/access convergence validation failed: "
            + (identity_access.stdout or identity_access.stderr).strip()
        )
    capability_convergence = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_research_os_capability_convergence.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    if capability_convergence.returncode != 0:
        fail(
            "Capability convergence validation failed: "
            + (capability_convergence.stdout or capability_convergence.stderr).strip()
        )
    governance = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_platform_governance.py")], cwd=ROOT, text=True, capture_output=True)
    if governance.returncode != 0:
        fail("platform governance validation failed: " + (governance.stdout or governance.stderr).strip())
    if "m2_audit:" not in text or "m2_audit_integrity_failure: STOP" not in text:
        fail("M.2 audit binding is incomplete")
    owner_special_bindings = (
        "  - .github/workflows/owner-special-build-identity-gate.yml",
        "  - .github/workflows/owner-special-friend.yml",
        "  - .github/workflows/owner-special-ios-ipa.yml",
        "  duplicate_platform_forbidden: true",
        "  duplicate_runtime_forbidden: true",
        "  duplicate_release_authority_forbidden: true",
        "  release_authority_remains: final_gate",
    )
    missing_owner = [item for item in owner_special_bindings if item not in text]
    if missing_owner:
        fail("Owner Special binding is incomplete: " + ", ".join(missing_owner))
    missing_spine = [item for item in EXPECTED_SPINE if f"  - {item}" not in text]
    if missing_spine:
        fail("unified spine is incomplete: " + ", ".join(missing_spine))
    print("UNIFIED_FINAL_GATE_CONTRACT=PASS")
    print("PLATFORM_CORE_COMPLETION=BOUND")
    print("100_PROJECT_READINESS=BOUND")
    print(f"NAVIGATION_REGISTRY={len(indexes)}_DESTINATIONS")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    print("DEFERRED_POLICY=EXPLICIT_AND_FAIL_CLOSED")
    print("AEOS_RECHECK=BOUND_TO_FINAL_GATE")
    print("AEOS_RELEASE_AUTHORITY=FINAL_GATE")
    runtime_resolution = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_platform_runtime_resolution.py")], cwd=ROOT, text=True, capture_output=True)
    if runtime_resolution.returncode != 0:
        fail("Platform runtime-resolution validation failed: " + (runtime_resolution.stdout or runtime_resolution.stderr).strip())
    print("IDENTITY_ACCESS_WAVE_1=BOUND_TO_FINAL_GATE")
    print("M2_AUDIT=BOUND_TO_FINAL_GATE")
    print("RUNTIME_RESOLUTION=BOUND_TO_PLATFORM")

if __name__ == "__main__":
    main()
