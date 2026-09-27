#!/usr/bin/env python3
"""Validate the long-term North Star and Digital Twin boundaries."""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NORTH_STAR = ROOT / "current/RESEARCH_OS_PLATFORM_NORTH_STAR_CONTRACT.json"
CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_DIGITAL_TWIN_CONTRACT.json"
INVENTORY = ROOT / "current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json"
FINAL_GATE = ROOT / "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"

def fail(message: str) -> None:
    print("PLATFORM_DIGITAL_TWIN=FAIL: " + message)
    raise SystemExit(1)

def main() -> int:
    for p in (NORTH_STAR, CONTRACT, INVENTORY, FINAL_GATE):
        if not p.is_file():
            fail("missing:" + str(p.relative_to(ROOT)))
    north = json.loads(NORTH_STAR.read_text(encoding="utf-8"))
    twin = json.loads(CONTRACT.read_text(encoding="utf-8"))
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    gate = FINAL_GATE.read_text(encoding="utf-8")
    for doc in (north, twin):
        a = doc.get("authority", {})
        if any(a.get(k) is not False for k in ("may_execute","may_authorize","may_approve","may_merge","may_release")):
            fail("future architecture acquired authority")
        if a.get("release_authority") != "FINAL_GATE":
            fail("release authority drift")
    if north.get("canonical_flow") != ["INTENT","GOVERNANCE","IDENTITY","CAPABILITY","POLICY","AUTHORIZATION","ENTITLEMENT","ADMISSION","EXECUTION","EVIDENCE","RECONCILIATION","LEARNING"]:
        fail("canonical north-star flow drift")
    if set(twin.get("operations", [])) != {"snapshot","impact","simulate"}:
        fail("digital twin operations drift")
    if "digital_twin" not in {c.get("id") for c in inv.get("components", [])}:
        fail("digital twin is not registered")
    for anchor in (
        "current/RESEARCH_OS_PLATFORM_NORTH_STAR_CONTRACT.json",
        "current/RESEARCH_OS_PLATFORM_DIGITAL_TWIN_CONTRACT.json",
        "platform_digital_twin:",
    ):
        if anchor not in gate:
            fail("Final Gate anchor missing:" + anchor)
    spine = subprocess.run([sys.executable, "tools/platform_spigital_twin.py"], cwd=ROOT, text=True, capture_output=True)
    if spine.returncode != 0:
        fail("digital twin execution failed:" + (spine.stdout or spine.stderr).strip())
    print("PLATFORM_NORTH_STAR=BOUND")
    print("PLATFORM_DIGITAL_TWIN=PASS")
    print("PLATFORM_DIGITAL_TWIN_AUTHORITY=READ_ONLY")
    print("PLATFORM_SIMULATION=COMPOSED")
    print("PLATFORM_RELEASE_AUTHORITY=FINAL_GATE")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
