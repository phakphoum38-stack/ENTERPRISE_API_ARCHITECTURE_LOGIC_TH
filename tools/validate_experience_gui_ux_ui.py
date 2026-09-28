#!/usr/bin/env python3
"""Fail-closed validator for the Research OS Experience GUI/UX/UI Contract."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
CONTRACT=Path("current/EXPERIENCE_GUI_UX_UI_CONTRACT.json")
IDENTITY={"product_id","surface_id","screen_id","component_id","implementation_target"}
WORKFLOWS={"gui","ux","ui","design_system","visual_regression","accessibility","release"}
def fingerprint(v):
    return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()
def validate(path=CONTRACT):
    d=json.loads(path.read_text(encoding="utf-8")); f=[]
    if d.get("contract_id")!="research-os-experience-gui-ux-ui-v1": f.append("invalid_contract_id")
    if d.get("plane")!="EXPERIENCE": f.append("invalid_plane")
    if set(d.get("identity",{}).get("required",[]))!=IDENTITY: f.append("identity_schema_mismatch")
    if set(d.get("workflow_ownership",{}))!=WORKFLOWS: f.append("workflow_ownership_mismatch")
    t=d.get("target_resolution",{})
    if t.get("missing_identity")!="HOLD" or t.get("ambiguous_identity")!="HOLD" or t.get("unknown_target")!="HOLD": f.append("target_resolution_not_fail_closed")
    e=d.get("evidence",{})
    if e.get("unknown_state")!="HOLD" or e.get("conflict_state")!="HOLD" or e.get("evidence_is_authority") is not False: f.append("evidence_boundary_violation")
    a=d.get("authority",{})
    for k in ("may_mutate_runtime_authority","may_grant_permissions","may_approve_reviews","may_merge","may_enable_auto_merge","may_rewrite_history"):
        if a.get(k) is not False: f.append("authority_boundary_violation:"+k)
    if a.get("owner_authority")!="unchanged" or a.get("merge_authority")!="unchanged": f.append("authority_changed")
    m=d.get("mathematical_root",{})
    if m!={"symbol":"10^1000","interpretation":"logical_coverage","materialization":"forbidden","execution":"bounded"}: f.append("mathematical_root_mismatch")
    return not f,f,fingerprint(d)
if __name__=="__main__":
    ok,f,fp=validate()
    print("experience_contract_sha256:",fp)
    for x in f: print("[FAIL]",x)
    if f: raise SystemExit(1)
    print("[PASS] EXPERIENCE_GUI_UX_UI_CONTRACT")
