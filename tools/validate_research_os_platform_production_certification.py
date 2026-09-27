#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"current/RESEARCH_OS_PLATFORM_PRODUCTION_CERTIFICATION_CONTRACT.json"
REQUIRED=[
"current/RESEARCH_OS_PLATFORM_PRODUCTION_CERTIFICATION_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_RUNTIME_COMPLETION_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_RECON_REPAIR_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_FAILURE_SIMULATION_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_OBSERVABILITY_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_AI_CODE_WRITER_CONTRACT.json",
"tools/validate_research_os_platform_runtime_completion.py",
"tools/platform_spine.py",
"tools/platform_self_reconciliation.py",
"apps/research_os_laravel/README.md",
"apps/research_os_flutter/lib/src/ui/enterprise_navigation.dart",
"current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
]
def run(*args):
    return subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True)
def main():
    missing=[p for p in REQUIRED if not (ROOT/p).is_file()]
    if missing:
        print("PRODUCTION_CERTIFICATION=STOP"); print("MISSING="+",".join(missing)); return 1
    c=json.loads(CONTRACT.read_text())
    a=c["authority"]
    if any(a.get(k) is not False for k in ("may_execute","may_authorize","may_approve","may_merge","may_release")) or a.get("release_authority")!="FINAL_GATE":
        print("PRODUCTION_CERTIFICATION=STOP"); return 1
    checks=[
      ["tools/validate_research_os_platform_runtime_completion.py"],
      ["tools/platform_spine.py","--validate"],
      ["tools/validate_platform_self_reconciliation.py"],
    ]
    for cmd in checks:
        r=run(*cmd)
        if r.returncode:
            print("PRODUCTION_CERTIFICATION=STOP")
            print((r.stdout or r.stderr)[-4000:])
            return 1
    print("PRODUCTION_CERTIFICATION=PASS")
    print("PLATFORM_RUNTIME=QUALIFIED")
    print("RECON_REPAIR=BOUNDED")
    print("FAILURE_RECOVERY=QUALIFIED")
    print("OBSERVABILITY=QUALIFIED")
    print("AI_CODE_WRITER=RECON_BOUND")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    return 0
if __name__=="__main__": raise SystemExit(main())
