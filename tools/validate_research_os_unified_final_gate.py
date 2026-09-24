#!/usr/bin/env python3
"""Validate the Research OS Unified Final Gate contract and its source anchors."""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_UNIFIED_FINAL_GATE.yml"

REQUIRED_FILES = (
    "current/CANONICAL_PLATFORM_CONTRACT.yml",
    "current/GOLDEN_RELEASE_CONTRACT.yml",
    ".github/workflows/research-os-gate.yml",
    ".github/workflows/research-os-final-gate.yml",
    ".github/workflows/research-os-platform-surface-matrix.yml",
    ".github/workflows/research-os-release-spine-gate.yml",
    "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart",
    "apps/research_os_flutter/test/platform_surface_parity_test.dart",
    "apps/research_os_flutter/test/desktop_shell_test.dart",
)

EXPECTED_SPINE = (
    "identity",
    "capability",
    "authorization",
    "navigation",
    "page_feature",
    "workflow",
    "event_queue",
    "stateless_runner",
    "evidence_provenance",
    "aeos_recheck",
    "final_gate",
    "release",
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

    navigation = (
        ROOT
        / "apps"
        / "research_os_flutter"
        / "lib"
        / "src"
        / "ui"
        / "enterprise_navigation.dart"
    ).read_text(encoding="utf-8")

    registry = navigation.split("const researchNavigationItems", 1)[1].split("];", 1)[0]
    entries = re.findall(
        r"ResearchNavItem\\((.*?)\\),\\s*(?=ResearchNavItem|$)",
        registry,
        flags=re.DOTALL,
    )
    indexes: list[int] = []
    for entry in entries:
        numbers = re.findall(r"\b(\d+)\b", entry)
        if not numbers:
            fail("navigation entry is missing a stable index")
        indexes.append(int(numbers[-1]))
    if len(indexes) != 15:
        fail(f"navigation registry contains {len(indexes)} entries; expected 15")
    if sorted(indexes) != list(range(15)):
        fail(f"navigation indexes drifted: {indexes}")

    missing_spine = [item for item in EXPECTED_SPINE if f"  - {item}" not in text]
    if missing_spine:
        fail("unified spine is incomplete: " + ", ".join(missing_spine))

    print("UNIFIED_FINAL_GATE_CONTRACT=PASS")
    print("NAVIGATION_REGISTRY=15_DESTINATIONS")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    print("DEFERRED_POLICY=EXPLICIT_AND_FAIL_CLOSED")


if __name__ == "__main__":
    main()
