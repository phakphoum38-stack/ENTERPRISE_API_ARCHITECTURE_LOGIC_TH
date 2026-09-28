#!/usr/bin/env python3
"""Validate the Research OS Platform from its schema-driven component registry."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json"
INVENTORY = ROOT / "current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json"
SCHEMA = ROOT / "current/RESEARCH_OS_PLATFORM_COMPONENT_REGISTRY_SCHEMA.json"
FINAL_GATE = ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"

REQUIRED_FILES = (
"current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json",
"current/RESEARCH_OS_PLATFORM_COMPONENT_REGISTRY_SCHEMA.json",
"current/RESEARCH_OS_PLATFORM_CORE_COMPLETION_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_DEFECT_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_SCHEDULE_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_RISK_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_CHANGE_IMPACT_CONTRACT.json",
"current/RESEARCH_OS_PRODUCT_SURFACE_INVENTORY_CONTRACT.json",
"current/RESEARCH_OS_100_PROJECT_READINESS_CONTRACT.json",
"current/RESEARCH_OS_PROJECT_SCALE_EXECUTION_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_PRODUCTION_HARDENING_CONTRACT.json",
"current/RESEARCH_OS_OWNER_EXPERIENCE_PLATFORM_CONTRACT.json",
"current/PLATFORM_INTEGRATION_CONTRACT.json",
"current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
"current/ARCHITECTURE_INVARIANTS.md",
"current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json",
"tools/platform_graph.py",
"tools/project_registry.py",
"tools/lifecycle_evidence.py",
"tools/research_os_api/universal_runner.py",
"tools/research_os_api/runner_installer.py",
"apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart",
"apps/research_os_flutter/lib/src/features/control_center/native_control_center_page.dart",
"apps/research_os_flutter/lib/src/features/owner/owner_experience_page.dart",
)

LIFECYCLES = ("PROPOSED","EXPERIMENTAL","ACTIVE","DEPRECATED","RETIRED")
REQUIRED_AUTHORITY_RULES = (
    "canonical_sources_remain_authoritative",
    "unknown_is_not_done",
    "missing_evidence_is_not_pass",
    "final_gate_is_single_release_authority",
)

def fail(msg: str) -> None:
    print("PLATFORM_ARCHITECTURE=FAIL: " + msg)
    raise SystemExit(1)

def validate_shape(data: dict, schema: dict) -> None:
    if data.get("schema_version") != schema["properties"]["schema_version"]["const"]:
        fail("component registry schema_version drifted")
    if data.get("status") != "ACTIVE":
        fail("component registry is not ACTIVE")
    if data.get("count_is_informational") is not True:
        fail("component count must remain informational only")
    if data.get("required_component_selection") != "component.required == true":
        fail("required component selection is not explicit")
    semantics=data.get("registry_semantics",{})
    if semantics.get("single_source_of_truth") is not True:
        fail("registry must remain the single component metadata source")
    if semantics.get("count_is_not_a_contract") is not True:
        fail("component count cannot become a contract")
    if set(data.get("lifecycle_model",[])) != set(LIFECYCLES):
        fail("lifecycle model drifted")
    if not {"CORE","PLATFORM","ASSURANCE","EXPERIENCE","EXTENSION"} <= set(data.get("classes",[])):
        fail("component classes incomplete")

def validate_components(inv: dict) -> dict[str, dict]:
    declared=inv.get("components",[])
    if not isinstance(declared,list) or not declared:
        fail("component registry is empty")
    ids=[c.get("id") for c in declared]
    if any(not isinstance(i,str) or not i for i in ids):
        fail("component id missing")
    if len(ids) != len(set(ids)):
        fail("duplicate platform component ids")
    comps={c["id"]:c for c in declared}
    required=[c for c in declared if c.get("required") is True]
    if not required:
        fail("no required platform components declared")
    for c in declared:
        cid=c["id"]
        for field in ("canonical","kind","class","lifecycle","dependencies","contracts","tests","evidence","gates","capabilities","authority","compatibility"):
            if field not in c:
                fail(f"{cid}.{field} missing")
        if c["lifecycle"] not in LIFECYCLES:
            fail(f"{cid}.lifecycle invalid")
        if c["required"] and c["lifecycle"] != "ACTIVE":
            fail(f"{cid} is required but lifecycle is {c['lifecycle']}")
        if c["lifecycle"] == "RETIRED" and c["required"]:
            fail(f"{cid} cannot be required when retired")
        if len(c["capabilities"]) != len(set(c["capabilities"])):
            fail(f"{cid}.capabilities duplicated")
        if not c["authority"].get("mode"):
            fail(f"{cid}.authority is not explicit")
        if not c["compatibility"].get("registry_schema") or not c["compatibility"].get("platform_contract"):
            fail(f"{cid}.compatibility incomplete")
        if c["lifecycle"] != "RETIRED":
            if not (ROOT/c["canonical"]).exists():
                fail(f"{cid}:canonical:{c['canonical']}")
            for ref in c["contracts"] + c["tests"] + c["evidence"]:
                if not (ROOT/ref).exists():
                    fail(f"{cid}:{ref}")
        for dep in c["dependencies"]:
            if dep not in comps:
                fail(f"{cid}:unknown dependency:{dep}")
    return comps

def main() -> None:
    if not CONTRACT.is_file(): fail("audit contract missing")
    missing=[p for p in REQUIRED_FILES if not (ROOT/p).is_file()]
    if missing: fail("missing canonical anchors: " + ", ".join(missing))
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
    schema=json.loads(SCHEMA.read_text(encoding="utf-8"))
    validate_shape(inv,schema)
    comps=validate_components(inv)
    registry_rule=contract.get("registry_validation",{})
    if registry_rule.get("registry") != "current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json":
        fail("audit contract registry binding drifted")
    if registry_rule.get("schema") != "current/RESEARCH_OS_PLATFORM_COMPONENT_REGISTRY_SCHEMA.json":
        fail("audit contract schema binding drifted")
    if registry_rule.get("required_selector") != "component.required == true":
        fail("audit contract required selector drifted")
    if registry_rule.get("count_policy") != "informational_only":
        fail("audit contract count policy drifted")
    rules=set(inv.get("rules",[]))
    for rule in REQUIRED_AUTHORITY_RULES:
        if rule not in rules:
            fail("component inventory rule missing: " + rule)
    gate=FINAL_GATE.read_text(encoding="utf-8")
    for anchor in ("release_authority: final_gate","m2_audit:","release_blocked_by_unresolved_deferred: true","platform_surface:"):
        if anchor not in gate:
            fail("final gate anchor missing: " + anchor)
    if "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json" not in gate:
        fail("platform architecture audit is not bound to Unified Final Gate")
    if "required_component_ids" in contract:
        fail("audit contract still carries a duplicated component id list")
    print("PLATFORM_ARCHITECTURE=PASS")
    print(f"PLATFORM_COMPONENTS={len(comps)}")
    print(f"PLATFORM_REQUIRED_COMPONENTS={sum(1 for c in comps.values() if c.get('required') is True)}")
    print("PLATFORM_COMPONENT_COUNT_POLICY=INFORMATIONAL_ONLY")
    print("PLATFORM_REGISTRY=SCHEMA_DRIVEN")
    print("PLATFORM_DOMAINS=CORE,CONTROL,EXECUTION,GOVERNANCE,SURFACES,SCALE,DISTRIBUTION")
    print("SHARED_EXECUTION_PLANE=REQUIRED")
    print("SHARED_EVIDENCE_PLANE=REQUIRED")
    print("OWNER_PRIVILEGE_BOUNDARY=UNBOUNDED")
    print("RESOURCE_CONFLICT=REJECT_AND_RELEASE")
    print("FINAL_GATE=SOLE_RELEASE_AUTHORITY")

if __name__ == "__main__":
    main()
