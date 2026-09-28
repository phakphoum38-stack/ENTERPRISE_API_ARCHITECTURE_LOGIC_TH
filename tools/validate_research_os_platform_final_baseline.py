#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT_PATH=ROOT/"current/RESEARCH_OS_PLATFORM_FINAL_BASELINE_CONTRACT.json"
def run_python(*args:str)->subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True)
def main()->int:
    c=json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if c.get("status")!="ACTIVE":
        print("PLATFORM_FINAL_BASELINE=STOP"); print("contract_status_invalid"); return 1
    missing=[p for p in c["required_contracts"]+c["required_implementation_anchors"] if not (ROOT/p).is_file()]
    if missing:
        print("PLATFORM_FINAL_BASELINE=STOP"); print("missing="+",".join(missing)); return 1
    laravel=json.loads((ROOT/"current/RESEARCH_OS_LARAVEL_PLATFORM_CONTRACT.json").read_text(encoding="utf-8"))
    if laravel.get("status")!="active":
        print("PLATFORM_FINAL_BASELINE=STOP"); print("laravel_contract_must_be_active"); return 1
    certification=json.loads((ROOT/"current/RESEARCH_OS_PLATFORM_PRODUCTION_CERTIFICATION_CONTRACT.json").read_text(encoding="utf-8"))
    if certification.get("release_authority")!="FINAL_GATE":
        print("PLATFORM_FINAL_BASELINE=STOP"); print("production_certification_release_authority_invalid"); return 1
    checks=[
        ("PLATFORM_SPINE",["tools/platform_spine.py","--validate"]),
        ("PRODUCTION_CERTIFICATION",["tools/validate_research_os_platform_production_certification.py"]),
        ("RUNTIME_QUALIFICATION",["-m","unittest","tools.test_platform_continuity_workflow","tools.test_platform_work_checkpoint","-v"]),
    ]
    for label,args in checks:
        r=run_python(*args)
        if r.returncode:
            print("PLATFORM_FINAL_BASELINE=STOP"); print(label+"=FAIL"); print((r.stdout or r.stderr)[-4000:]); return 1
    print("PLATFORM_FINAL_BASELINE=PASS")
    print("PLATFORM_SPINE=PASS")
    print("PRODUCTION_CERTIFICATION=PASS")
    print("RUNTIME_QUALIFICATION=PASS")
    print("LARAVEL_BOUNDARY=ACTIVE")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    print("CI_EVIDENCE=REQUIRED")
    print("EXACT_SOURCE_SHA=REQUIRED")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
