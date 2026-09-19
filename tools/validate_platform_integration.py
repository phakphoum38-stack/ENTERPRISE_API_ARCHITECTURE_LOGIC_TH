#!/usr/bin/env python3
"""Fail-closed validator for the Research OS Platform Integration Contract."""
from __future__ import annotations
import hashlib, json
from pathlib import Path
CONTRACT = Path("current/PLATFORM_INTEGRATION_CONTRACT.json")
PLANES={"CORE","ASSURANCE","PLATFORM","EXPERIENCE"}
DUPLICATES={"global_scheduler","worker_pool","task_queue","memory_store","learning_root","resource_control_plane","provider_credential_engine","assurance_engine","merge_authority","branch_protection_controller"}
AUTH={"platform_may_compose","platform_may_mutate_core_authority","platform_may_grant_permissions","platform_may_approve_reviews","platform_may_merge","platform_may_enable_auto_merge","platform_may_rewrite_history","owner_authority","merge_authority"}
def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def validate(path=CONTRACT):
    d=json.loads(path.read_text(encoding="utf-8")); f=[]
    if d.get("contract_id")!="research-os-platform-integration-v1": f.append("invalid_contract_id")
    if d.get("version")!=1: f.append("invalid_version")
    if set(d.get("planes",{}))!=PLANES: f.append("plane_set_mismatch")
    a=d.get("authority",{})
    if set(a)!=AUTH: f.append("authority_keys_mismatch")
    if a.get("platform_may_compose") is not True: f.append("platform_composition_not_enabled")
    for k in ("platform_may_mutate_core_authority","platform_may_grant_permissions","platform_may_approve_reviews","platform_may_merge","platform_may_enable_auto_merge","platform_may_rewrite_history"):
        if a.get(k) is not False: f.append("authority_boundary_violation:"+k)
    if a.get("owner_authority")!="unchanged": f.append("owner_authority_changed")
    if a.get("merge_authority")!="unchanged": f.append("merge_authority_changed")
    if set(d.get("forbidden_duplicate_subsystems",[]))!=DUPLICATES: f.append("duplicate_subsystem_guard_mismatch")
    e=d.get("evidence_contract",{})
    if e.get("unknown_state")!="HOLD": f.append("unknown_not_fail_closed")
    if e.get("conflict_state")!="HOLD": f.append("conflict_not_fail_closed")
    if e.get("evidence_is_authority") is not False: f.append("evidence_authority_leak")
    if d.get("mathematical_root")!={"symbol":"10^1000","interpretation":"logical_coverage","materialization":"forbidden","execution":"bounded"}: f.append("mathematical_root_mismatch")
    return not f,f,canonical_sha256(d)
if __name__=="__main__":
    ok,f,fp=validate(); print("platform_contract_sha256:",fp)
    [print("[FAIL]",x) for x in f]
    if f: raise SystemExit(1)
    print("[PASS] PLATFORM_INTEGRATION_CONTRACT")
