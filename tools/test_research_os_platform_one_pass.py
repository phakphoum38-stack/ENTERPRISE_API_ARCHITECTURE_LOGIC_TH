#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_ONE_PASS_COMPLETION_CONTRACT.json"
INVENTORY = ROOT / "current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json"
def test_contract_and_validator():
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert contract["status"] == "ACTIVE"
    assert contract["authority"]["release_authority"] == "FINAL_GATE"
    result = subprocess.run([sys.executable,"tools/validate_research_os_platform_one_pass.py"],cwd=ROOT,text=True,capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PLATFORM_ONE_PASS=PASS" in result.stdout
def test_registered_component():
    inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
    component = next(c for c in inventory["components"] if c["id"] == "platform_one_pass_completion")
    assert component["required"] is True
    assert component["lifecycle"] == "ACTIVE"
    assert component["authority"]["mode"] == "NONE"
