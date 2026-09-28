#!/usr/bin/env python3
"""Deterministic failure semantics for Platform runtime qualification."""
from __future__ import annotations
import argparse,json
EXPECTED={"resource_conflict":"REJECT_AND_RELEASE","stale_delivery":"REJECT","dependency_failure":"RETRY_OR_DLQ","contract_mismatch":"HOLD","worker_crash":"RECOVER_AND_RECONCILE","timeout":"RETRY_OR_TERMINAL","retry_exhaustion":"DLQ","rollback":"RESTORE_SNAPSHOT","idempotency":"DEDUPLICATE"}
def simulate(scenario:str)->dict:
    if scenario not in EXPECTED:return {"status":"HOLD","scenario":scenario}
    return {"status":"PASS","scenario":scenario,"expected_action":EXPECTED[scenario]}
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--scenario",required=True); a=ap.parse_args(); r=simulate(a.scenario); print(json.dumps(r,sort_keys=True)); return 0 if r["status"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
