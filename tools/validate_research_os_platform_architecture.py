#!/usr/bin/env python3
"""Validate the complete Research OS Platform architecture against existing authorities."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json"
INVENTORY=ROOT/"current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json"
FINAL_GATE=ROOT/"current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"

REQUIRED_FILES=(
"current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json",
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

REQUIRED_IDS=(
"platform_workspace","platform_graph","navigation","product_surface","project_identity",
"workflow","evidence","control_center","release","owner","defect_control","schedule_control",
"risk_control","change_impact_control","memory_fabric","universal_runner","runner_installation",
"owner_experience_platform",
)

def fail(msg:str)->None:
    print("PLATFORM_ARCHITECTURE=FAIL: "+msg)
    raise SystemExit(1)

def main()->None:
    if not CONTRACT.is_file(): fail("audit contract missing")
    missing=[p for p in REQUIRED_FILES if not (ROOT/p).is_file()]
    if missing: fail("missing canonical anchors: "+", ".join(missing))
    contract=json.loads(CONTRACT.read_text(encoding="utf-8"))
    inv=json.loads(INVENTORY.read_text(encoding="utf-8"))
    comps={c["id"]:c for c in inv.get("components",[])}
    missing_ids=[i for i in REQUIRED_IDS if i not in comps]
    if missing_ids: fail("missing component inventory ids: "+", ".join(missing_ids))
    bad=[]
    for cid in REQUIRED_IDS:
        c=comps[cid]
        for field in ("canonical","kind","lifecycle","contracts","tests","evidence","gates"):
            if field not in c: bad.append(f"{cid}.{field}")
        if c.get("lifecycle")!="ACTIVE": bad.append(f"{cid}.lifecycle")
        if not c.get("contracts") or not c.get("tests") or not c.get("evidence") or not c.get("gates"):
            bad.append(f"{cid}.proof")
        for ref in c.get("contracts",[])+c.get("tests",[])+c.get("evidence",[]):
            if not (ROOT/ref).exists(): bad.append(f"{cid}:{ref}")
    if bad: fail("component proof incomplete: "+", ".join(sorted(set(bad))))
    rules=set(inv.get("rules",[]))
    for rule in ("canonical_sources_remain_authoritative","unknown_is_not_done","missing_evidence_is_not_pass","final_gate_is_single_release_authority"):
        if rule not in rules: fail("component inventory rule missing: "+rule)
    text=FINAL_GATE.read_text(encoding="utf-8")
    for anchor in ("release_authority: final_gate","m2_audit:","release_blocked_by_unresolved_deferred: true","platform_surface:"):
        if anchor not in text: fail("final gate anchor missing: "+anchor)
    if "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json" not in text:
        fail("platform architecture audit is not bound to Unified Final Gate")
    if set(contract["required_component_ids"]) != set(REQUIRED_IDS):
        fail("audit contract component set drifted")
    inv_text=json.dumps(inv)
    for marker in ("final_gate_is_single_release_authority","nvme_is_storage_backed_memory_not_dram","unknown_runner_capability_is_not_available"):
        if marker not in inv_text: fail("platform inventory rule missing: "+marker)
    print("PLATFORM_ARCHITECTURE=PASS")
    print(f"PLATFORM_COMPONENTS={len(comps)}")
    print("PLATFORM_DOMAINS=CORE,CONTROL,EXECUTION,GOVERNANCE,SURFACES,SCALE,DISTRIBUTION")
    print("SHARED_EXECUTION_PLANE=REQUIRED")
    print("SHARED_EVIDENCE_PLANE=REQUIRED")
    print("OWNER_PRIVILEGE_BOUNDARY=UNBOUNDED")
    print("RESOURCE_CONFLICT=REJECT_AND_RELEASE")
    print("FINAL_GATE=SOLE_RELEASE_AUTHORITY")

if __name__=="__main__":
    main()
