#!/usr/bin/env python3
"""Validate Schedule reconciliation against the existing Research OS platform."""
from __future__ import annotations
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
 "contract":"current/RESEARCH_OS_PLATFORM_SCHEDULE_CONTRACT.json",
 "completion_contract":"current/RESEARCH_OS_PLATFORM_COMPLETION_SCHEDULE_CONTRACT.json",
 "generator_models":"owner_special/research_os_friend/schedule_generation/models.py",
 "generator":"owner_special/research_os_friend/schedule_generation/generator.py",
 "adapter":"owner_special/research_os_friend/schedule_generation/adapter.py",
 "preview":"owner_special/research_os_friend/schedule_generation/preview.py",
 "service":"owner_special/research_os_friend/service.py",
 "tests":"owner_special/tests/test_schedule_generation.py",
 "operating_control_tests":"tools/test_platform_operating_control.py",
 "control_center":"apps/research_os_flutter/lib/src/features/control_center/native_control_center_page.dart",
 "final_gate":"current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
 "final_gate_validator":"tools/validate_research_os_unified_final_gate.py",
}
def fail(message:str)->None:
 print(f"PLATFORM_SCHEDULE_COMPLETION=FAIL: {message}"); raise SystemExit(1)
def main()->None:
 missing=[p for p in REQUIRED.values() if not (ROOT/p).is_file()]
 if missing: fail("missing anchors: "+", ".join(missing))
 schedule=json.loads((ROOT/REQUIRED["contract"]).read_text(encoding="utf-8"))
 completion=json.loads((ROOT/REQUIRED["completion_contract"]).read_text(encoding="utf-8"))
 if schedule.get("status")!="ACTIVE": fail("schedule contract is not ACTIVE")
 authority=schedule.get("authority",{})
 if authority.get("descriptive_only") is not True: fail("schedule authority is not descriptive-only")
 for key in ("may_execute","may_authorize","may_release"):
  if authority.get(key) is not False: fail(f"schedule {key} must be false")
 if authority.get("release_authority")!="FINAL_GATE": fail("schedule release authority drifted")
 for rule in ("schedule_is_not_a_runtime","schedule_does_not_replace_existing_queue","dependencies_are_explicit","blocked_work_is_not_done","done_requires_verification","deferred_is_not_done","final_gate_remains_single_release_authority"):
  if rule not in schedule.get("rules",[]): fail(f"missing canonical schedule rule: {rule}")
 if completion.get("status")!="ACTIVE": fail("completion contract is not ACTIVE")
 if completion.get("release_authority")!="FINAL_GATE": fail("completion release authority drifted")
 adapter=(ROOT/REQUIRED["adapter"]).read_text(encoding="utf-8")
 service=(ROOT/REQUIRED["service"]).read_text(encoding="utf-8")
 control=(ROOT/REQUIRED["control_center"]).read_text(encoding="utf-8")
 gate=(ROOT/REQUIRED["final_gate"]).read_text(encoding="utf-8")
 if "class ScheduleGenerateTool" not in adapter or 'name = "schedule.generate"' not in adapter: fail("deterministic schedule generation boundary missing")
 if "/owner/schedule/previews/" not in service or "/confirm" not in service: fail("schedule preview/confirmation boundary missing")
 if "schedule_control" not in control or "RESEARCH_OS_PLATFORM_SCHEDULE_CONTRACT" not in control: fail("Control Center schedule projection missing")
 if "current/RESEARCH_OS_PLATFORM_COMPLETION_SCHEDULE_CONTRACT.json" not in gate: fail("completion contract is not bound to Unified Final Gate")
 if "tools/validate_platform_completion_schedule.py" not in gate: fail("schedule completion validator is not bound to Unified Final Gate")
 if "tools/test_platform_completion_schedule.py" not in gate: fail("schedule completion test is not bound to Unified Final Gate")
 for marker in ('"release_authority": "SCHEDULE"','"authorization_authority": "SCHEDULE"','"execution_authority": "SCHEDULE"',"ScheduleScheduler"):
  if marker in adapter or marker in service: fail(f"duplicate scheduler authority marker found: {marker}")
 print("PLATFORM_SCHEDULE_COMPLETION=PASS")
 print("SCHEDULE_CONTRACT=ACTIVE")
 print("SCHEDULE_GENERATION=BOUND")
 print("SCHEDULE_PREVIEW=BOUND")
 print("CONTROL_CENTER_PROJECTION=BOUND")
 print("NO_SECOND_SCHEDULER_AUTHORITY=PASS")
 print("RELEASE_AUTHORITY=FINAL_GATE")
if __name__=="__main__": main()
