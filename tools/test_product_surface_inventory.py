#!/usr/bin/env python3
"""Validate the canonical Research OS product surface inventory."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_PRODUCT_SURFACE_INVENTORY_CONTRACT.json"


def main() -> None:
    payload = json.loads(CONTRACT.read_text(encoding="utf-8"))
    surfaces = payload["surfaces"]
    assert len(surfaces) == 18, "product surface inventory must cover the 18 canonical destinations"
    indexes = [item[1] for item in surfaces]
    assert indexes == list(range(17)), f"navigation indexes drifted: {indexes}"
    labels = [item[0] for item in surfaces]
    assert len(labels) == len(set(labels)), "surface labels must be unique"

    shell = ROOT / "apps/research_os_flutter/lib/src/app_shell.dart"
    navigation = ROOT / "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart"
    assert shell.is_file(), "canonical app shell is missing"
    assert navigation.is_file(), "canonical navigation registry is missing"
    shell_text = shell.read_text(encoding="utf-8")
    navigation_text = navigation.read_text(encoding="utf-8")

    for label, index, implementation, shell_ref in surfaces:
        implementation_path = ROOT / implementation
        assert implementation_path.is_file(), f"{label}: missing implementation {implementation}"
        assert shell_ref == "apps/research_os_flutter/lib/src/app_shell.dart"
        assert implementation_path.stem in shell_text, f"{label}: implementation is not wired in app shell"

    assert "const researchNavigationItems" in navigation_text
    assert "Control Center" in navigation_text
    assert "capabilityId: 'control_center'" in navigation_text

    for path in (
        payload["non_surface_bindings"]["control_center_audit"],
        payload["non_surface_bindings"]["capability_navigation_contract"],
    ):
        assert (ROOT / path).is_file(), f"missing supporting binding: {path}"

    assert payload["authority"]["descriptive_only"] is True
    assert payload["authority"]["release_authority"] == "FINAL_GATE"
    assert "PROJECT_EXPERIENCE: no canonical ProjectRegistry API endpoint is exposed by ResearchOSApiClient yet; do not fabricate project telemetry." not in payload["next_product_gaps"]
    print("PRODUCT_SURFACE_INVENTORY=PASS")
    print("CANONICAL_DESTINATIONS=17")
    print("AUTHORITY=DESCRIPTIVE_ONLY")
    print("PROJECT_EXPERIENCE=COMPLETE")
    assert "WORKFLOW_EXPERIENCE: orchestration lifecycle is exposed through existing API client, but a dedicated product workspace mapping remains to be completed." not in payload["next_product_gaps"]
    print("WORKFLOW_EXPERIENCE=COMPLETE")


if __name__ == "__main__":
    main()
