#!/usr/bin/env python3
"""Validate the single Flutter navigation-to-capability convergence boundary."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_CAPABILITY_CONVERGENCE_CONTRACT.json"
NAVIGATION = ROOT / "apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart"
REGISTRY = ROOT / "tools/control_center_capability_registry.py"


def fail(message: str) -> None:
    raise SystemExit(f"CAPABILITY_CONVERGENCE=FAIL: {message}")


def _navigation_entries(text: str) -> dict[str, tuple[int, str | None]]:
    marker = "const researchNavigationItems"
    if marker not in text:
        fail("navigation registry declaration is missing")
    body = text.split(marker, 1)[1].split("];", 1)[0]
    matches = re.findall(r"ResearchNavItem\((.*?)\),\s*(?=ResearchNavItem|$)", body, re.DOTALL)
    entries: dict[str, tuple[int, str | None]] = {}
    for raw in matches:
        destination = re.search(r"destinationId:\s*'([^']+)'", raw)
        index = re.findall(r"\b(\d+)\b", raw)
        if destination is None or not index:
            fail("navigation entry is missing destinationId or stable index")
        capability = re.search(r"capabilityId:\s*'([^']+)'", raw)
        key = destination.group(1)
        if key in entries:
            fail(f"duplicate navigation destination: {key}")
        entries[key] = (int(index[-1]), capability.group(1) if capability else None)
    if not entries:
        fail("navigation registry is empty")
    return entries


def main() -> int:
    if not CONTRACT.is_file():
        fail(f"missing contract: {CONTRACT.relative_to(ROOT)}")
    if not NAVIGATION.is_file() or not REGISTRY.is_file():
        fail("required authority files are missing")

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    if contract.get("contract_id") != "research-os-capability-convergence-v1":
        fail("contract id mismatch")
    if contract.get("status") != "ACTIVE":
        fail("contract is not ACTIVE")

    nav = _navigation_entries(NAVIGATION.read_text(encoding="utf-8"))
    if sorted(index for index, _ in nav.values()) != list(range(len(nav))):
        fail("navigation indexes are not contiguous")
    if len(nav) != 18:
        fail(f"unexpected navigation destination count: {len(nav)}")

    bindings = contract.get("bindings", [])
    by_destination = {item.get("destination_id"): item for item in bindings}
    if len(by_destination) != len(bindings):
        fail("duplicate convergence binding destination")
    if set(by_destination) - set(nav):
        fail("binding references an unknown navigation destination")

    registry_text = REGISTRY.read_text(encoding="utf-8")
    registry_ids = set(re.findall(r'CapabilityBinding\(\s*"([^"]+)"', registry_text))
    for destination, item in by_destination.items():
        capability = item.get("capability_id")
        authority = item.get("authority")
        if item.get("status") != "BOUND":
            fail(f"{destination}: unsupported binding status")
        actual = nav[destination][1]
        if actual != capability:
            fail(f"{destination}: navigation capabilityId drifted")
        if destination == "owner":
            if authority != "owner_experience_contract":
                fail("owner binding must use the Owner Experience contract")
        elif capability not in registry_ids:
            fail(f"{destination}: capability is not present in canonical registry")
        elif authority != "backend_capability_registry":
            fail(f"{destination}: backend capability authority is required")

    for destination, (_, capability) in nav.items():
        binding = by_destination.get(destination)
        if binding is None:
            if capability is not None:
                fail(f"{destination}: untracked capability metadata")
            continue
        if capability != binding["capability_id"]:
            fail(f"{destination}: capability binding mismatch")

    rules = contract.get("rules", [])
    required_rules = {
        "navigation_registry_remains_single_source_of_truth",
        "capability_id_is_identity_metadata_only",
        "authorization_remains_outside_flutter",
        "execution_remains_delegated_to_existing_runtime_or_executor",
        "owner_identity_is_server_derived_and_unbounded_by_resource_or_scope",
        "no_new_runtime",
        "no_new_authorization_authority",
        "no_new_navigation_registry",
    }
    missing = sorted(required_rules - set(rules))
    if missing:
        fail("missing fail-closed rules: " + ", ".join(missing))

    unbound = contract.get("unbound_policy", {})
    if unbound.get("status") != "HOLD" or unbound.get("must_not_infer_permission") is not True:
        fail("unbound policy must be explicit HOLD and non-authorizing")

    print("CAPABILITY_CONVERGENCE=PASS")
    print(f"NAVIGATION_DESTINATIONS={len(nav)}")
    print(f"BOUND_CAPABILITIES={len(bindings)}")
    print("AUTHORIZATION_AUTHORITY=EXTERNAL")
    print("EXECUTION_AUTHORITY=DELEGATED")
    print("OWNER_AUTHORITY=SERVER_DERIVED_UNBOUNDED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
