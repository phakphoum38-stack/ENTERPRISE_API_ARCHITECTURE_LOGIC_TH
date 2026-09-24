"""Finite Platform Core Definition-of-Done validator.

This validator reconciles existing canonical contracts and implementation
boundaries. It does not execute workloads and does not create authority.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_CORE_COMPLETION_CONTRACT.json"
READINESS_CONTRACT = ROOT / "current/RESEARCH_OS_100_PROJECT_READINESS_CONTRACT.json"

REQUIRED_FILES = (
    "current/CANONICAL_PLATFORM_CONTRACT.yml",
    "current/GOLDEN_RELEASE_CONTRACT.yml",
    "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
    "current/RESEARCH_OS_PHASE_B_LIFECYCLE_EVIDENCE_CONTRACT.json",
    "current/RESEARCH_OS_PHASE_C_CAPABILITY_E2E_BINDING_CONTRACT.json",
    "current/RESEARCH_OS_PHASE_D_CROSS_SURFACE_PARITY_CONTRACT.json",
    "current/RESEARCH_OS_PHASE_E_UNIFIED_WINDOWS_DISTRIBUTION_CONTRACT.json",
    "tools/capability_delegation.py",
    "tools/capability_e2e_binding.py",
    "tools/lifecycle_evidence.py",
    "tools/control_center_capability_registry.py",
    "tools/native_command_router.py",
    "tools/validate_canonical_platform_contract.py",
    "tools/validate_research_os_unified_final_gate.py",
    "tools/validate_phase_e_unified_windows_distribution.py",
)

MARKERS = (
    ("tools/capability_delegation.py", "CANONICAL_DELEGATIONS"),
    ("tools/capability_e2e_binding.py", "class CapabilityE2EBinding"),
    ("tools/lifecycle_evidence.py", "class LifecycleEvidence"),
    ("tools/control_center_capability_registry.py", "CANONICAL_CAPABILITY_BINDINGS"),
    ("tools/native_command_router.py", "simulation"),
)

def validate(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"missing required platform-core component: {rel}")

    if not CORE_CONTRACT.exists() or not READINESS_CONTRACT.exists():
        return tuple(errors)

    core = json.loads(CORE_CONTRACT.read_text(encoding="utf-8"))
    readiness = json.loads(READINESS_CONTRACT.read_text(encoding="utf-8"))

    if core.get("status") != "ACTIVE":
        errors.append("platform core completion contract is not ACTIVE")
    if readiness.get("project_count") != 100:
        errors.append("100-project readiness count must be exactly 100")

    invariants = core.get("invariants", {})
    for key, expected in (
        ("shared_execution_plane", True),
        ("shared_evidence_plane", True),
        ("single_final_gate", True),
        ("owner_is_unbounded_privilege_boundary", True),
        ("external_tools_are_not_authority", True),
        ("assurance_is_not_executable", True),
        ("platform_specific_navigation_is_forbidden", True),
        ("source_sha_is_exact_identity", True),
        ("resource_conflict_is_reject_and_release", True),
        ("duplicate_delivery_is_idempotent", True),
        ("unknown_state_fails_closed", True),
    ):
        if invariants.get(key) is not expected:
            errors.append(f"core invariant missing: {key}")

    for invariant in readiness.get("required_invariants", ()):
        if not isinstance(invariant, str) or not invariant:
            errors.append("100-project readiness contains invalid invariant")

    if readiness.get("scale_test", {}).get("contexts") != 100:
        errors.append("100-project scale test must instantiate exactly 100 contexts")

    for rel, marker in MARKERS:
        path = root / rel
        if path.exists() and marker not in path.read_text(encoding="utf-8"):
            errors.append(f"implementation marker missing: {rel}:{marker}")

    return tuple(errors)


if __name__ == "__main__":
    failures = validate()
    if failures:
        for item in failures:
            print(f"PLATFORM_CORE=FAIL: {item}")
        raise SystemExit(1)
    print("PLATFORM_CORE=PASS")
    print("100_PROJECT_READINESS=BOUND")
