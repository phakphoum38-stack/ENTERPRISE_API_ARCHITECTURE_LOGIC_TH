#!/usr/bin/env python3
"""Validate the complete Research OS Platform Spine as one canonical composition."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_ONE_PASS_COMPLETION_CONTRACT.json"
INVENTORY = ROOT / "current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json"
FINAL_GATE = ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"
REQUIRED = [
    "current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json",
    "current/RESEARCH_OS_PLATFORM_COMPONENT_REGISTRY_SCHEMA.json",
    "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_CHANGE_IMPACT_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_SELF_RECONCILIATION_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_RUNTIME_READINESS_CONTRACT.json",
    "current/PLATFORM_OPERATIONALIZATION_CONTRACT.json",
    "current/RESEARCH_OS_PLATFORM_SERVICE_CONTRACT.json",
    "tools/platform_graph.py",
    "tools/platform_service.py",
    "tools/platform_self_reconciliation.py",
    "tools/platform_runtime_readiness.py",
    "tools/platform_operationalization.py",
    "current/RESEARCH_OS_PLATFORM_SPINE_ENGINE_CONTRACT.json",
    "tools/platform_spine.py",
    "tools/test_platform_spine.py",
    "tools/validate_platform_self_reconciliation.py",
    "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
]
AUTHORITY_FALSE = ("may_execute","may_authorize","may_approve","may_merge","may_release")

def fail(message: str) -> None:
    print("PLATFORM_ONE_PASS=FAIL: " + message)
    raise SystemExit(1)

def has_cycle(graph: dict[str, list[str]]) -> bool:
    visiting, visited = set(), set()
    def visit(node: str) -> bool:
        if node in visiting: return True
        if node in visited: return False
        visiting.add(node)
        for dep in graph.get(node, []):
            if visit(dep): return True
        visiting.remove(node)
        visited.add(node)
        return False
    return any(visit(node) for node in graph)

def main() -> int:
    if not CONTRACT.is_file(): fail("completion contract missing")
    missing = [p for p in REQUIRED if not (ROOT / p).is_file()]
    if missing: fail("missing canonical anchors: " + ", ".join(missing))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    gate = FINAL_GATE.read_text(encoding="utf-8")
    if contract.get("status") != "ACTIVE": fail("completion contract is not ACTIVE")
    authority = contract.get("authority", {})
    if any(authority.get(k) is not False for k in AUTHORITY_FALSE): fail("completion layer acquired authority")
    if authority.get("release_authority") != "FINAL_GATE": fail("release authority drifted")
    rules = set(contract.get("rules", []))
    required_rules = {"reuse_existing_capabilities","no_duplicate_runtime","no_duplicate_authorization","no_duplicate_evidence","no_duplicate_queue","no_duplicate_registry_authority","no_duplicate_release_authority","platform_is_composition_layer"}
    if not required_rules <= rules: fail("completion invariants incomplete")
    components = inventory.get("components", [])
    ids = {c.get("id") for c in components}
    if "platform_one_pass_completion" not in ids: fail("one-pass completion component is not registered")
    component = next(c for c in components if c.get("id") == "platform_one_pass_completion")
    if component.get("lifecycle") != "ACTIVE" or component.get("required") is not True: fail("completion component must be required and ACTIVE")
    if component.get("authority", {}).get("mode") != "NONE": fail("completion component must have NONE authority")
    graph = {c["id"]: list(c.get("dependencies", [])) for c in components}
    unknown = sorted({d for deps in graph.values() for d in deps if d not in graph})
    if unknown: fail("unknown dependencies: " + ", ".join(unknown))
    if has_cycle(graph): fail("dependency cycle detected")
    lifecycle = contract.get("lifecycle", {})
    transitions = {tuple(t) for t in lifecycle.get("allowed_transitions", [])}
    expected = {("PROPOSED","EXPERIMENTAL"),("EXPERIMENTAL","ACTIVE"),("ACTIVE","DEPRECATED"),("DEPRECATED","RETIRED")}
    if transitions != expected: fail("lifecycle transition model drifted")
    if lifecycle.get("backward_transition") != "FORBIDDEN": fail("backward lifecycle transition is not forbidden")
    compatibility = contract.get("compatibility", {})
    if compatibility.get("breaking_change") != "NEW_CONTRACT_VERSION_AND_MIGRATION": fail("breaking compatibility rule drifted")
    if compatibility.get("unknown_compatibility") != "HOLD": fail("unknown compatibility is not fail-closed")
    impact = contract.get("change_impact", {})
    if set(impact.get("required_categories", [])) != {"contracts","workflows","tests","final_gate","invariants","product_surfaces"}: fail("change-impact categories incomplete")
    health = contract.get("health", {})
    if set(health.get("states", [])) != {"READY","DEGRADED","BLOCKED","RETIRED"}: fail("health model incomplete")
    if health.get("health_is_not_authorization") is not True: fail("health/authorization boundary missing")
    security = contract.get("security", {})
    if security.get("chain") != ["Identity","Capability","Policy","Authorization","Entitlement","Execution","Evidence"]: fail("security chain drifted")
    if security.get("resource_conflict") != "REJECT_AND_RELEASE": fail("resource conflict policy drifted")
    runtime = contract.get("runtime", {})
    if runtime.get("direct_engine_to_runner") is not False: fail("direct Engine -> Runner is not forbidden")
    if runtime.get("execution_pattern") != "Engine -> Event/Queue -> Stateless Worker": fail("runtime execution pattern drifted")
    for anchor in ("release_authority: final_gate","release_blocked_by_unresolved_deferred: true","platform_service:","self_reconciliation:","runtime_readiness:"):
        if anchor not in gate: fail("final gate anchor missing: " + anchor)
    if "current/RESEARCH_OS_PLATFORM_ONE_PASS_COMPLETION_CONTRACT.json" not in gate: fail("completion contract is not bound to Final Gate")
    if "current/RESEARCH_OS_PLATFORM_SPINE_ENGINE_CONTRACT.json" not in gate: fail("spine engine contract is not bound to Final Gate")
    if "tools/platform_spine.py" not in gate or "tools/test_platform_spine.py" not in gate: fail("spine engine is not bound to Final Gate")
    spine = subprocess.run([sys.executable, "tools/platform_spine.py", "--validate"], cwd=ROOT, text=True, capture_output=True)
    if spine.returncode != 0:
        fail("Platform Spine engine validation failed: " + (spine.stdout or spine.stderr).strip())
    print("PLATFORM_ONE_PASS=PASS")
    print("PLATFORM_SPINE=COMPLETE")
    print("PLATFORM_REGISTRY=SCHEMA_DRIVEN")
    print("PLATFORM_DEPENDENCY_GRAPH=VALID")
    print("PLATFORM_LIFECYCLE=VALID")
    print("PLATFORM_COMPATIBILITY=VALID")
    print("PLATFORM_CHANGE_IMPACT=BOUND")
    print("PLATFORM_RECON=BOUND")
    print("PLATFORM_REPAIR_BOUNDARY=FAIL_CLOSED")
    print("PLATFORM_HEALTH=BOUND")
    print("PLATFORM_DRIFT=BOUND")
    print("PLATFORM_SECURITY=BOUND")
    print("PLATFORM_RUNTIME=QUEUE_TO_STATELESS_WORKER")
    print("PLATFORM_RELEASE_AUTHORITY=FINAL_GATE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
