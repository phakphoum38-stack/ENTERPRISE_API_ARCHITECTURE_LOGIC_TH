#!/usr/bin/env python3
"""Phase D cross-surface parity validator.

Read-only: reconciles existing registries/contracts and never executes a capability.
"""
from __future__ import annotations

import json
from pathlib import Path

from tools.capability_delegation import CANONICAL_DELEGATIONS, validate_delegations
from tools.control_center_capability_registry import CANONICAL_CAPABILITY_BINDINGS, validate_registry

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_PHASE_D_CROSS_SURFACE_PARITY_CONTRACT.json"

EXPECTED = {"control_center", "friend", "agent", "github", "factory_v3", "assurance"}
DELEGATED = {"friend", "agent", "github", "factory_v3", "assurance"}


def validate(root: Path = ROOT) -> tuple[str, ...]:
    errors: list[str] = []
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))

    if set(contract["capabilities"]) != EXPECTED:
        errors.append("phase D capability set drifted")

    registry = {item.capability_id: item for item in CANONICAL_CAPABILITY_BINDINGS}
    if set(registry) != EXPECTED:
        errors.append("capability registry does not cover the canonical capability set")
    errors.extend(validate_registry())

    delegations = {item.capability_id: item for item in CANONICAL_DELEGATIONS}
    if set(delegations) != DELEGATED:
        errors.append("delegation set drifted")
    errors.extend(validate_delegations())

    # Registry executor_ref may name a concrete runtime adapter while the
    # delegation registry names the contract-facing executor. Phase D therefore
    # reconciles by canonical capability ownership, not string identity:
    # every delegated capability must have a non-empty runtime/executor pair,
    # and the delegation executor must remain the canonical executor family.
    expected_executor_families = {
        "friend": "FriendRuntime",
        "agent": "AgentRuntime",
        "github": "github_status.py",
        "factory_v3": "FactoryExecutionEngine",
        "assurance": "EvidenceRecorder",
    }
    for capability_id in DELEGATED:
        binding = registry.get(capability_id)
        delegation = delegations.get(capability_id)
        if binding is None or delegation is None:
            continue
        expected = expected_executor_families[capability_id]
        if expected not in binding.runtime_ref and expected not in binding.executor_ref:
            errors.append(f"{capability_id}: registry executor family mismatch")
        if expected not in delegation.executor_ref:
            errors.append(f"{capability_id}: delegation executor family mismatch")

    assurance = delegations.get("assurance")
    if assurance is not None and (assurance.execution_supported or assurance.operations):
        errors.append("assurance must remain non-executable")

    phase_b = json.loads(
        (root / "current" / "RESEARCH_OS_PHASE_B_LIFECYCLE_EVIDENCE_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    required = set(phase_b["required_evidence_fields"])
    if set(contract["required_evidence_fields"]) != required:
        errors.append("phase D evidence field set differs from Phase B")

    gate = (root / ".github/workflows/research-os-unified-final-gate.yml").read_text(
        encoding="utf-8"
    )
    if "tools.test_phase_d_cross_surface_parity" not in gate:
        errors.append("Unified Final Gate is missing the Phase D parity test")

    platform = (root / ".github/workflows/research-os-platform-surface-matrix.yml").read_text(
        encoding="utf-8"
    )
    for name in contract["required_platforms"]:
        if f"platform: {name}" not in platform:
            errors.append(f"platform matrix missing {name}")
    if "platform_specific_navigation_registry: forbidden" not in (
        root / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"
    ).read_text(encoding="utf-8"):
        errors.append("Unified Final Gate does not forbid platform-specific navigation registries")

    return tuple(errors)


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"PHASE_D_PARITY=FAIL: {error}")
        return 1
    print("PHASE_D_PARITY=PASS")
    print("CAPABILITIES=6")
    print("DELEGATED_EXECUTORS=5")
    print("PLATFORMS=windows,web,ios")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
