#!/usr/bin/env python3
"""Bounded runtime for deterministic Recon repair planning."""
from __future__ import annotations
import argparse,json,subprocess
from pathlib import Path
from tools.platform_self_reconciliation import tracked_files,resolve_path,build_plan,is_protected,replace_reference
ROOT=Path(__file__).resolve().parents[1]
def plan(reference:str, owner_file:str, source_sha:str="UNKNOWN")->dict:
    files=tracked_files(ROOT); r=resolve_path(reference,files)
    if r.status=="AMBIGUOUS": return {"status":"STOP","reason":"AMBIGUOUS_TARGET","candidates":list(r.candidates)}
    if r.status=="MISSING": return {"status":"HOLD","reason":"MISSING_TARGET"}
    if r.status=="FOUND": return {"status":"NOOP","target":r.target}
    if is_protected(r.target or ""): return {"status":"STOP","reason":"PROTECTED_CORE"}
    p=build_plan(source_sha,owner_file,r)
    return {"status":"PLAN","repair":p.__dict__,"snapshot_required":True,"sandbox_required":True,"rollback_required":True}
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--reference",required=True); ap.add_argument("--file",required=True); ap.add_argument("--source-sha",default="UNKNOWN"); a=ap.parse_args()
    result=plan(a.reference,a.file,a.source_sha); print(json.dumps(result,sort_keys=True)); return 0 if result["status"] in {"PLAN","NOOP"} else 1
if __name__=="__main__": raise SystemExit(main())
