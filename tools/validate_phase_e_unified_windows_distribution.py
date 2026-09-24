#!/usr/bin/env python3
"""Validate the Phase E unified Windows distribution contract and staging rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_PHASE_E_UNIFIED_WINDOWS_DISTRIBUTION_CONTRACT.json"

REQUIRED_COMPONENTS = {
    "research_os_flutter",
    "research_os_python",
    "tools",
    "platform",
    "assurance",
    "owner_special",
    "workflow_tooling",
    "runtime_python",
}

REQUIRED_PACKAGE_PATHS = {
    "app/research_os_flutter.exe",
    "owner_special/app/research_os_owner_special.exe",
    "owner_special/OWNER_MANIFEST.json",
    "owner_special/research_os_friend",
    "owner_special/scripts",
    "tools",
    "v3",
    "current",
    "workflow",
    "runtime/python/python.exe",
    "service_host/ResearchOS.ServiceHost.exe",
    "service_host/ResearchOS.Owner.ServiceHost.exe",
    "scripts/research-os-service.ps1",
}


def validate(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    if set(contract["required_components"]) != REQUIRED_COMPONENTS:
        errors.append("phase E required component set drifted")
    if set(contract["required_package_paths"]) != REQUIRED_PACKAGE_PATHS:
        errors.append("phase E required package path set drifted")

    identity = contract["identity"]
    if identity["product_name"] != "Research OS":
        errors.append("main product identity drifted")
    if identity["company_name"] != "Research OS Team":
        errors.append("main company identity drifted")
    if identity["main_executable"] != "research_os_flutter.exe":
        errors.append("main executable identity drifted")
    if identity["owner_executable"] != "research_os_owner_special.exe":
        errors.append("Owner Special executable identity drifted")

    provenance = contract["provenance"]
    for key in (
        "source_sha_required",
        "manifest_required",
        "sha256_required",
        "source_sha_must_match_manifest",
        "artifact_sha256_required",
    ):
        if provenance.get(key) is not True:
            errors.append(f"provenance invariant missing: {key}")

    authority = contract["authority"]
    for key in (
        "final_gate_remains_release_authority",
        "owner_authorization_remains_authoritative",
        "external_tools_are_not_authority",
        "distribution_is_not_execution_authority",
    ):
        if authority.get(key) is not True:
            errors.append(f"authority invariant missing: {key}")

    workflow = (root / ".github/workflows/research-os-phase-e-unified-windows-distribution.yml").read_text(
        encoding="utf-8"
    )
    for marker in (
        "TARGET_SHA",
        "Research-OS-Unified-Windows-x64",
        "SHA256SUMS.txt",
        "RESEARCH_OS_UNIFIED_WINDOWS_DISTRIBUTION",
        "research_os_owner_special.exe",
        "runtime\\python\\python.exe",
    ):
        if marker not in workflow:
            errors.append(f"Phase E workflow missing required marker: {marker}")

    gate = (root / ".github/workflows/research-os-unified-final-gate.yml").read_text(
        encoding="utf-8"
    )
    if "tools.test_phase_e_unified_windows_distribution" not in gate:
        errors.append("Unified Final Gate is missing the Phase E distribution test")

    return tuple(errors)


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"PHASE_E_DISTRIBUTION=FAIL: {error}")
        return 1
    print("PHASE_E_DISTRIBUTION=PASS")
    print("COMPONENTS=8")
    print("PACKAGE_PATHS=13")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
