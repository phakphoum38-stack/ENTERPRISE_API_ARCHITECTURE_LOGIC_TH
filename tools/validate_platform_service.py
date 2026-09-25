#!/usr/bin/env python3
"""Fail-closed validator for the reusable Platform composition layer."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = (
    "current/RESEARCH_OS_PLATFORM_SERVICE_CONTRACT.json",
    "current/PLATFORM_PROJECT_SNAPSHOT_CONTRACT.json",
    "current/RESEARCH_OS_M2_PLATFORM_CONTRACT.json",
    "tools/platform_service.py",
    "tools/test_platform_service.py",
    "tools/research_os_m2_platform.py",
    "tools/platform_graph.py",
    "tools/project_registry.py",
    "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
)

FORBIDDEN_AUTHORITY_FLAGS = (
    "may_execute",
    "may_authorize",
    "may_approve",
    "may_merge",
    "may_release",
)


def validate() -> list[str]:
    failures: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).is_file():
            failures.append(f"missing:{rel}")

    if failures:
        return failures

    service = json.loads(
        (ROOT / "current/RESEARCH_OS_PLATFORM_SERVICE_CONTRACT.json").read_text()
    )
    snapshot = json.loads(
        (ROOT / "current/PLATFORM_PROJECT_SNAPSHOT_CONTRACT.json").read_text()
    )
    if service.get("status") != "ACTIVE":
        failures.append("service_contract_not_active")
    authority = service.get("authority", {})
    for key in FORBIDDEN_AUTHORITY_FLAGS:
        if authority.get(key) is not False:
            failures.append(f"service_authority_violation:{key}")
    if authority.get("release_authority") != "FINAL_GATE":
        failures.append("service_release_authority")
    invariants = service.get("invariants", {})
    for key in (
        "shared_execution_plane",
        "shared_evidence_plane",
        "no_per_project_runtime",
        "no_per_project_queue",
        "no_per_project_evidence_ledger",
        "external_tools_are_not_authority",
        "unknown_is_not_pass",
        "deferred_is_not_done",
        "chat_is_not_source_of_truth",
    ):
        if invariants.get(key) is not True:
            failures.append(f"invariant_missing:{key}")

    required_snapshot = set(snapshot.get("required_fields", []))
    expected_snapshot = {
        "repository", "source_sha", "protected_baseline_sha", "active_work",
        "deferred_work", "decisions", "verified_truths", "evidence_refs",
        "open_risks", "unknowns", "authority_boundaries", "next_action",
    }
    if required_snapshot != expected_snapshot:
        failures.append("snapshot_schema_drift")

    text = (ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml").read_text()
    for anchor in (
        "platform_service:",
        "continuity:",
        "current/RESEARCH_OS_PLATFORM_SERVICE_CONTRACT.json",
        "current/PLATFORM_PROJECT_SNAPSHOT_CONTRACT.json",
        "release_authority: final_gate",
    ):
        if anchor not in text:
            failures.append(f"final_gate_anchor_missing:{anchor}")

    py = (ROOT / "tools/platform_service.py").read_text()
    for marker in (
        "class PlatformService",
        "def recon",
        "def impact",
        "def snapshot",
        "def resume",
        "PlatformGraph.from_paths",
        "ProjectRegistry",
        "M2Platform",
    ):
        if marker not in py:
            failures.append(f"implementation_marker_missing:{marker}")

    m2 = (ROOT / "tools/research_os_m2_platform.py").read_text()
    if "RESEARCH_OS_M2_PLATFORM_CONTRACT.json" not in m2:
        failures.append("m2_contract_binding_missing")

    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("PLATFORM_COMPLETE=FAIL")
        print(*failures, sep="\n")
        return 1
    print("PLATFORM_COMPLETE=PASS")
    print("COMPOSITION=CANONICAL_SUBSYSTEMS")
    print("RUNTIME_DUPLICATION=FORBIDDEN")
    print("CHAT_AS_AUTHORITY=FORBIDDEN")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    print("SNAPSHOT_SHA_PINNING=REQUIRED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
