#!/usr/bin/env python3
"""Validate executable Platform runtime completion boundaries."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/"current/RESEARCH_OS_PLATFORM_RUNTIME_COMPLETION_CONTRACT.json"
REQUIRED=[
"current/RESEARCH_OS_PLATFORM_RUNTIME_COMPLETION_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_RECON_REPAIR_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_FAILURE_SIMULATION_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_OBSERVABILITY_CONTRACT.json",
"current/RESEARCH_OS_PLATFORM_AI_CODE_WRITER_CONTRACT.json",
"tools/platform_repair_engine.py","tools/test_platform_repair_engine.py",
"tools/platform_failure_simulator.py","tools/test_platform_failure_simulator.py",
"tools/platform_observability.py","tools/test_platform_observability.py",
"tools/platform_code_writer.py","tools/test_platform_code_writer.py",
"apps/research_os_laravel/src/Platform/Infrastructure/CanonicalToolGateway.php",
"apps/research_os_laravel/src/Platform/Infrastructure/CanonicalControlGateway.php",
"apps/research_os_laravel/src/Platform/Infrastructure/CanonicalOperationsGateway.php",
"apps/research_os_laravel/src/Platform/Application/ToolApplicationService.php",
"apps/research_os_laravel/src/Platform/Application/ControlApplicationService.php",
"apps/research_os_laravel/src/Platform/Application/OperationsApplicationService.php",
"apps/research_os_laravel/src/Platform/Application/ConfigurationService.php",
"apps/research_os_laravel/src/Platform/Application/VersionApplicationService.php",
"apps/research_os_laravel/src/Platform/Http/PlatformController.php",
"apps/research_os_laravel/src/Platform/Http/VersionController.php",
"apps/research_os_laravel/tests/Unit/PlatformRuntimeTest.php",
]
def run(*args): return subprocess.run([sys.executable,*args],cwd=ROOT,text=True,capture_output=True)
def main()->int:
    missing=[p for p in REQUIRED if not (ROOT/p).is_file()]
    if missing: print("PLATFORM_RUNTIME_COMPLETION=FAIL: missing "+", ".join(missing)); return 1
    c=json.loads(CONTRACT.read_text())
    if c.get("authority",{}).get("may_release") is not False or c.get("authority",{}).get("release_authority")!="FINAL_GATE":
        print("PLATFORM_RUNTIME_COMPLETION=FAIL: authority boundary"); return 1
    if c["runtime"]["direct_engine_to_runner"] is not False or not c["runtime"]["resource_conflict_fail_closed"]:
        print("PLATFORM_RUNTIME_COMPLETION=FAIL: runtime invariant"); return 1
    for test in ["tools.test_platform_repair_engine","tools.test_platform_failure_simulator","tools.test_platform_observability","tools.test_platform_code_writer"]:
        r=run("-m","unittest",test)
        if r.returncode: print("PLATFORM_RUNTIME_COMPLETION=FAIL: "+test+" "+(r.stdout or r.stderr)); return 1
    print("PLATFORM_RUNTIME_COMPLETION=PASS")
    print("LARAVEL_RUNTIME=BOUND")
    print("RECON_REPAIR=BOUNDED")
    print("FAILURE_SIMULATION=BOUND")
    print("OBSERVABILITY=BOUND")
    print("AI_CODE_WRITER=RECON_BOUND")
    print("RELEASE_AUTHORITY=FINAL_GATE")
    return 0
if __name__=="__main__": raise SystemExit(main())
