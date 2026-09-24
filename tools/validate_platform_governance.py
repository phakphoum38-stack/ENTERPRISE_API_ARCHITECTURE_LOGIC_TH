#!/usr/bin/env python3
"""Validate Research OS platform governance using existing canonical sources only."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from tools.platform_graph import PlatformGraph

ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate() -> list[str]:
    failures: list[str] = []
    contract = _load("current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json")
    if not contract.get("change_impact_rules"):
        failures.append("change_impact_rules_missing")
    if contract.get("contract_id") != "research-os-platform-governance-v1":
        failures.append("contract_id")
    if contract.get("status") != "ACTIVE":
        failures.append("contract_not_active")
    authority = contract.get("authority", {})
    for key in ("may_execute", "may_authorize", "may_approve", "may_merge", "may_release"):
        if authority.get(key) is not False:
            failures.append(f"authority:{key}")
    if authority.get("release_authority") != "FINAL_GATE":
        failures.append("release_authority")
    if authority.get("must_not_create_duplicate_authority") is not True:
        failures.append("duplicate_authority_policy")
    for source in contract.get("canonical_sources", {}).values():
        if not (ROOT / source).is_file():
            failures.append(f"missing_source:{source}")

    domains = contract.get("authority_domains", [])
    domain_names = [d.get("domain") for d in domains]
    if len(domain_names) != len(set(domain_names)):
        failures.append("duplicate_authority_domain")
    if len([d for d in domains if d.get("domain") == "release" and d.get("canonical") == "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"]) != 1:
        failures.append("release_domain_not_unique")

    workspace = _load("current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json")
    try:
        graph = PlatformGraph.from_paths("current/PLATFORM_VIRTUAL_WORKSPACE_CONTRACT.json", "current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json")
        failures.extend(f"platform_graph:{item}" for item in graph.validate())
    except Exception as exc:
        failures.append(f"platform_graph:error:{exc}")
    records = workspace.get("records", [])
    work_ids = [r.get("work_id") for r in records]
    paths = [r.get("virtual_path") for r in records]
    if len(work_ids) != len(set(work_ids)):
        failures.append("workspace_duplicate_work_id")
    if len(paths) != len(set(paths)):
        failures.append("workspace_duplicate_virtual_path")
    for record in records:
        if record.get("status") == "DONE" and record.get("resolution") == "UNKNOWN":
            failures.append(f"unknown_done:{record.get('work_id')}")

    surface = _load("current/RESEARCH_OS_PRODUCT_SURFACE_INVENTORY_CONTRACT.json")
    surfaces = surface.get("surfaces", [])
    indexes = [item[1] for item in surfaces]
    labels = [item[0] for item in surfaces]
    if len(indexes) != len(set(indexes)):
        failures.append("surface_duplicate_index")
    if len(labels) != len(set(labels)):
        failures.append("surface_duplicate_label")
    if sorted(indexes) != list(range(len(indexes))):
        failures.append("surface_indexes_not_contiguous")

    navigation = (ROOT / "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart").read_text(encoding="utf-8")
    marker = "const researchNavigationItems"
    if marker not in navigation:
        failures.append("navigation_registry_missing")
    else:
        registry = navigation.split(marker, 1)[1].split("];", 1)[0]
        entries = [part.split("),", 1)[0] for part in registry.split("ResearchNavItem(")[1:]]
        nav_indexes: list[int] = []
        destination_ids: list[str] = []
        for entry in entries:
            marker = "destinationId: '"
            if marker not in entry:
                failures.append("navigation_entry_missing_destination_id")
            else:
                destination_ids.append(entry.split(marker, 1)[1].split("'", 1)[0])
            numbers = re.findall("[0-9]+", entry)
            if not numbers:
                failures.append("navigation_entry_missing_index")
            else:
                nav_indexes.append(int(numbers[-1]))
        if len(nav_indexes) != len(surfaces):
            failures.append("navigation_surface_count_drift")
        if sorted(nav_indexes) != list(range(len(nav_indexes))):
            failures.append("navigation_indexes_not_contiguous")
        if len(nav_indexes) != len(set(nav_indexes)):
            failures.append("navigation_duplicate_index")
        if len(destination_ids) != len(set(destination_ids)):
            failures.append("navigation_duplicate_destination_id")

    invariants = (ROOT / "current/ARCHITECTURE_INVARIANTS.md").read_text(encoding="utf-8")
    for needle in ("INV-014", "INV-018", "INV-020", "INV-021", "INV-025", "Enforcement Principle"):
        if needle not in invariants:
            failures.append(f"invariant_anchor_missing:{needle}")
    gate = (ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml").read_text(encoding="utf-8")
    if "release_authority: final_gate" not in gate:
        failures.append("final_gate_authority_missing")
    if "navigation_drift: STOP" not in gate:
        failures.append("navigation_fail_closed_missing")
    return failures


def main() -> int:
    failures = validate()
    if failures:
        print("RESEARCH_OS_PLATFORM_GOVERNANCE=FAIL")
        print(*failures, sep="\\n")
        return 1
    print("RESEARCH_OS_PLATFORM_GOVERNANCE=PASS")
    print("AUTHORITY_MODEL=DESCRIPTIVE_VALIDATING")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    print("NAVIGATION_SOURCE=CANONICAL_REGISTRY")
    print("UNKNOWN_IS_NOT_PASS=TRUE")
    print("DUPLICATE_AUTHORITY=FORBIDDEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
