#!/usr/bin/env python3
"""Deterministic, read-only Platform Digital Twin projection."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any

from platform_spine import PlatformSpine

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "current/RESEARCH_OS_PLATFORM_DIGITAL_TWIN_CONTRACT.json"

class PlatformDigitalTwin:
    def __init__(self, root: Path = ROOT) -> None:
        self.root = root
        self.spine = PlatformSpine(root)
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    def snapshot(self) -> dict[str, Any]:
        components = self.spine.components
        nodes = []
        edges = []
        for cid in sorted(components):
            c = components[cid]
            nodes.append({
                "id": cid,
                "class": c.get("class"),
                "lifecycle": c.get("lifecycle"),
                "health": c.get("health", "UNSPECIFIED"),
                "authority": c.get("authority", {}).get("mode"),
            })
            for dep in sorted(c.get("dependencies", [])):
                edges.append({"from": cid, "to": dep})
        return {
            "contract_id": self.contract["contract_id"],
            "status": "PASS",
            "source": "canonical_platform_component_inventory",
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": nodes,
            "edges": edges,
            "authority": "READ_ONLY_PROJECTION",
            "release_authority": "FINAL_GATE",
        }

    def impact(self, targets: list[str], blast_radius: str = "COMPONENT") -> dict[str, Any]:
        return {
            "status": "PASS",
            "projection": "DIGITAL_TWIN",
            "result": self.spine.impact(targets, blast_radius),
            "mutation": False,
            "authorization": False,
            "release_authority": "FINAL_GATE",
        }

    def simulate(self, targets: list[str], blast_radius: str = "COMPONENT") -> dict[str, Any]:
        result = self.spine.simulate(targets, blast_radius)
        return {
            "projection": "DIGITAL_TWIN",
            "status": result.get("status"),
            "result": result,
            "mutation": False,
            "authorization": False,
            "release_authority": "FINAL_GATE",
        }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--impact", nargs="+")
    parser.add_argument("--simulate", nargs="+")
    parser.add_argument("--blast-radius", default="COMPONENT",
                        choices=("LOCAL","COMPONENT","PROJECT","CROSS_PROJECT","PLATFORM"))
    args = parser.parse_args()
    twin = PlatformDigitalTwin()
    if args.impact:
        print(json.dumps(twin.impact(args.impact, args.blast_radius), sort_keys=True))
        return 0
    if args.simulate:
        result = twin.simulate(args.simulate, args.blast_radius)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "PASS" else 1
    print(json.dumps(twin.snapshot(), sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
