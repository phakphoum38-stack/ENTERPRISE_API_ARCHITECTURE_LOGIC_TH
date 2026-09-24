#!/usr/bin/env python3
"""Validate the Research OS Unified Final Gate contract and its source anchors."""
from __future__ import annotations
from pathlib import Path
import re

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
    "tools/test_project_registry.py",
    ".github/workflows/research-os-gate.yml",
    ".github/workflows/research-os-final-gate.yml",
    ".github/workflows/research-os-platform-surface-matrix.yml",
    ".github/workflows/research-os-phase-e-unified-windows-distribution.yml",
    ".github/workflows/research-os-release-spine-gate.yml",
    ".github/workflows/research-os-unified-final-gate.yml",
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
        numbers = re.findall(r"\b(\d+)\b", entry)
        if not numbers:
            fail("navigation entry is missing a stable index")
        indexes.append(int(numbers[-1]))
    if len(indexes) != 18:
        fail(f"navigation registry contains {len(indexes)} entries; expected 18")
    if sorted(indexes) != list(range(18)):
        fail(f"navigation indexes drifted: {indexes}")
    missing_spine = [item for item in EXPECTED_SPINE if f"  - {item}" not in text]
    if missing_spine:
        fail("unified spine is incomplete: " + ", ".join(missing_spine))
    print("UNIFIED_FINAL_GATE_CONTRACT=PASS")
    print("PLATFORM_CORE_COMPLETION=BOUND")
    print("100_PROJECT_READINESS=BOUND")
    print("NAVIGATION_REGISTRY=17_DESTINATIONS")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    print("DEFERRED_POLICY=EXPLICIT_AND_FAIL_CLOSED")

if __name__ == "__main__":
    main()
