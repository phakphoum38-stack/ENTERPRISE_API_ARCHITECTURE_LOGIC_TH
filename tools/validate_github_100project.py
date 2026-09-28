#!/usr/bin/env python3
"""Fail-closed structural validator for the GitHub 100PROJECT assurance contract."""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/"current"/"GITHUB_100PROJECT_CONTINUOUS_ASSURANCE_CONTRACT.json"
ALLOWED={"PASS","FAIL","HOLD","UNKNOWN","UNAVAILABLE","NOT_APPLICABLE","INSUFFICIENT_SCOPE"}

def fingerprint(obj: object)->str:
    raw=json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    return hashlib.sha256(raw).hexdigest()

def validate(doc:dict)->list[str]:
    e=[]
    if doc.get("contract")!="GITHUB_100PROJECT_CONTINUOUS_ASSURANCE": e.append("wrong_contract")
    if doc.get("protocol")!="100PROJECT": e.append("wrong_protocol")
    if doc.get("fail_closed") is not True: e.append("fail_closed_required")
    if doc.get("unknown_policy")!="HOLD": e.append("unknown_must_hold")
    if doc.get("merge_authority")!="RECON_OWNER_AUTHORITY_UNCHANGED": e.append("merge_authority_boundary_changed")
    surfaces=doc.get("surfaces")
    if not isinstance(surfaces,list) or len(surfaces)!=100: e.append("surface_count_must_equal_100")
    else:
        ids=[x[0] if isinstance(x,list) and len(x)==2 else None for x in surfaces]
        if ids!= [f"P{i:02d}" for i in range(1,101)]: e.append("surface_ids_not_contiguous")
        if len(set(ids))!=100: e.append("surface_ids_not_unique")
    states=doc.get("state_values")
    if states!=sorted(states,key=lambda x:["PASS","FAIL","HOLD","UNKNOWN","UNAVAILABLE","NOT_APPLICABLE","INSUFFICIENT_SCOPE"].index(x)): e.append("state_values_changed")
    if not set(doc.get("required_fields",[]))=={"control_id","surface","observed_state","checked_at","source_ref","evidence_fingerprint","scope_state"}: e.append("required_fields_changed")
    forbidden=doc.get("mutation_boundary",{}).get("forbidden",[])
    for x in ("change_branch_protection","grant_permissions","approve_reviews","merge_pull_requests","enable_auto_merge","rewrite_canonical_history","disable_required_checks"):
        if x not in forbidden: e.append("missing_forbidden:"+x)
    if not isinstance(doc.get("termination",{}).get("drain_only_when"),list): e.append("termination_contract_missing")
    return e

def main()->int:
    p=argparse.ArgumentParser(); p.add_argument("--contract",default=str(DEFAULT)); p.add_argument("--print-fingerprint",action="store_true"); a=p.parse_args()
    doc=json.loads(Path(a.contract).read_text(encoding="utf-8"))
    errors=validate(doc)
    if errors:
        print("FAIL"); print("\n".join(errors)); return 1
    print("PASS")
    print(f"surface_count={len(doc['surfaces'])}")
    if a.print_fingerprint: print("contract_fingerprint="+fingerprint(doc))
    return 0

if __name__=="__main__": raise SystemExit(main())
