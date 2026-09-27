#!/usr/bin/env python3
REQUIRED=("REGISTRY","RECON","DEPENDENCY_GRAPH","CONTRACT","CHANGE_BOUNDARY","CODE_WRITER","VALIDATION","EVIDENCE")
def plan(stages:list[str])->dict:
    unknown=[s for s in stages if s not in REQUIRED]
    if unknown:return {"status":"HOLD","unknown":unknown}
    missing=[s for s in REQUIRED if s not in stages]
    if missing:return {"status":"HOLD","missing":missing}
    return {"status":"PASS","pipeline":list(REQUIRED),"main_direct_write":False,"must_not_invent_canonical_authority":True}
