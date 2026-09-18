#!/usr/bin/env python3
"""Fail-closed validator for the metadata-only Platform Virtual Workspace."""
import argparse,hashlib,json,sys
from pathlib import Path
C={"FOUNDATION","INTEGRATION","EVOLUTION","FEDERATION","RESOURCE","SECURITY","RELEASE","OPERATIONS"}
S={"PLANNED","IN_PROGRESS","BLOCKED","HOLD","UNKNOWN","DONE","SUPERSEDED"}
R={"FOUND","PARTIAL","GAP","UNKNOWN"}
def validate(contract,registry):
    f=[]
    if contract.get("contract_id")!="research-os-platform-virtual-workspace-v1": f.append("contract_id")
    ids=set(); paths=set()
    records=registry.get("records")
    if not isinstance(records,list) or not records: f.append("records")
    for x in records or []:
        for k in contract["required_record_fields"]:
            if k not in x: f.append(f"missing:{x.get('work_id','?')}:{k}")
        if x.get("work_id") in ids:f.append(f"duplicate_work_id:{x.get('work_id')}")
        if x.get("virtual_path") in paths:f.append(f"duplicate_virtual_path:{x.get('virtual_path')}")
        ids.add(x.get("work_id"));paths.add(x.get("virtual_path"))
        if x.get("category") not in C:f.append(f"category:{x.get('work_id')}")
        if x.get("status") not in S:f.append(f"status:{x.get('work_id')}")
        if x.get("resolution") not in R:f.append(f"resolution:{x.get('work_id')}")
        if not x.get("source_refs"):f.append(f"source_refs:{x.get('work_id')}")
        if x.get("resolution")=="UNKNOWN" and x.get("status")=="DONE":f.append(f"unknown_done:{x.get('work_id')}")
    a=contract.get("authority",{})
    if a.get("descriptive_only") is not True or any(a.get(k) is not False for k in ("may_merge","may_approve","may_grant_permissions","may_change_branch_protection","may_rewrite_history")):f.append("authority")
    payload=json.dumps({"contract":contract,"registry":registry},sort_keys=True,separators=(",",":")).encode()
    if f: raise ValueError(";".join(f))
    return hashlib.sha256(payload).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument("--contract",default="current/PLATFORM_VIRTUAL_WORKSPACE_CONTRACT.json");p.add_argument("--registry",default="current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json");a=p.parse_args()
    try:c=json.loads(Path(a.contract).read_text());r=json.loads(Path(a.registry).read_text());fp=validate(c,r)
    except Exception as e:print("PLATFORM_VIRTUAL_WORKSPACE=FAIL");print(e);return 1
    print("PLATFORM_VIRTUAL_WORKSPACE=PASS");print("registry_fingerprint:"+fp);print("record_count:"+str(len(r["records"])));return 0
if __name__=="__main__":sys.exit(main())
