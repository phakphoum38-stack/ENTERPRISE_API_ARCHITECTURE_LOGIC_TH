#!/usr/bin/env python3
"""Compute bounded change impact from the canonical governance contract."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json"

def impact(paths: list[str]) -> dict[str, list[str]]:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    components: set[str] = set()
    gates: set[str] = set()
    matched: dict[str, list[str]] = {}
    for raw in paths:
        path = raw.replace("\\", "/").lstrip("./")
        hits: list[str] = []
        for rule in contract.get("change_impact_rules", []):
            match = str(rule.get("match", "")).rstrip("/")
            if match and (path == match or path.startswith(match)):
                components.update(rule.get("components", []))
                gates.update(rule.get("gates", []))
                hits.append(match)
        if hits:
            matched[path] = hits
    return {"changed_paths": paths, "affected_components": sorted(components), "required_gates": sorted(gates), "matched_rules": matched}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    print(json.dumps(impact(args.paths), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
