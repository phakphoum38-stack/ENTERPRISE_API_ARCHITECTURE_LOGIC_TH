#!/usr/bin/env python3
"""Reusable Platform composition facade.

The service composes existing canonical subsystems. It is deliberately
read-only: it discovers, validates, traces and prepares continuity state but
does not execute work, authorize users, merge branches, or release artifacts.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

from tools.platform_graph import PlatformGraph
from tools.project_registry import PROJECT_001, ProjectRegistry, validate_registry
from tools.research_os_m2_platform import M2Platform

ROOT = Path(__file__).resolve().parents[1]


def canonical_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


class PlatformService:
    """Single composition boundary for Platform discovery and continuity."""

    def __init__(self) -> None:
        self.m2 = M2Platform()
        self.projects = ProjectRegistry((PROJECT_001,))

    def recon(self) -> dict[str, Any]:
        graph = PlatformGraph.from_paths(
            ROOT / "current/PLATFORM_VIRTUAL_WORKSPACE_CONTRACT.json",
            ROOT / "current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json",
        )
        failures = graph.validate()
        return {
            "source_sha": canonical_sha(),
            "m2_source_sha": self.m2.source_sha,
            "platform_graph": graph.summary(),
            "platform_graph_failures": failures,
            "project_registry_failures": list(validate_registry(self.projects.all())),
            "authority": "descriptive_composition_only",
        }

    def search(self, query: str, limit: int = 256) -> dict[str, Any]:
        return {
            "source_sha": canonical_sha(),
            "results": self.m2.search(query, limit=limit),
        }

    def vertical(self, query: str, depth: int = 10) -> dict[str, Any]:
        return self.m2.vertical(query, depth=depth)

    def horizontal(self, query: str, limit: int = 256) -> dict[str, Any]:
        return self.m2.horizontal(query, limit=limit)

    def impact(self, query: str) -> dict[str, Any]:
        return self.m2.impact(query)

    def project_validate(self) -> dict[str, Any]:
        errors = validate_registry(self.projects.all())
        return {
            "source_sha": canonical_sha(),
            "project_count": len(self.projects.all()),
            "errors": list(errors),
            "status": "PASS" if not errors else "HOLD",
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "repository": "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            "source_sha": canonical_sha(),
            "protected_baseline_sha": canonical_sha(),
            "active_work": ["platform-complete-build"],
            "deferred_work": [
                "flutter_windows_analyze_test_failures",
            ],
            "decisions": [
                "platform_is_the_reusable_root",
                "research_os_is_a_product_surface",
                "external_flutter_is_a_tool_not_platform_authority",
                "final_gate_is_single_release_authority",
            ],
            "verified_truths": [
                "m2_platform_service_is_read_only",
                "execution_plane_is_shared",
                "project_registry_uses_shared_queue_and_evidence",
            ],
            "evidence_refs": [
                "current/RESEARCH_OS_M2_PLATFORM_CONTRACT.json",
                "current/RESEARCH_OS_PLATFORM_ARCHITECTURE_AUDIT_CONTRACT.json",
                "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml",
            ],
            "open_risks": [],
            "unknowns": [],
            "authority_boundaries": {
                "platform_may_execute": False,
                "platform_may_authorize": False,
                "platform_may_approve": False,
                "platform_may_merge": False,
                "platform_may_release": False,
                "release_authority": "FINAL_GATE",
            },
            "next_action": "recon_then_impact_check_before_mutation",
        }

    def resume(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        required = {
            "repository", "source_sha", "protected_baseline_sha", "active_work",
            "deferred_work", "decisions", "verified_truths", "evidence_refs",
            "open_risks", "unknowns", "authority_boundaries", "next_action",
        }
        missing = sorted(required - set(snapshot))
        current = canonical_sha()
        failures: list[str] = []
        if missing:
            failures.append("missing_required_fields:" + ",".join(missing))
        if snapshot.get("source_sha") != current:
            failures.append("source_sha_mismatch")
        if snapshot.get("unknowns"):
            failures.append("unknowns_present")
        if snapshot.get("authority_boundaries", {}).get("release_authority") != "FINAL_GATE":
            failures.append("release_authority_boundary")
        return {
            "status": "HOLD" if failures else "READY_FOR_RECON",
            "current_sha": current,
            "snapshot_sha": snapshot.get("source_sha"),
            "failures": failures,
            "deferred_work": snapshot.get("deferred_work", []),
            "next_action": "run_platform_recon_and_impact" if not failures else "repair_snapshot_then_reverify",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recon", action="store_true")
    parser.add_argument("--query")
    parser.add_argument("--vertical", action="store_true")
    parser.add_argument("--horizontal", action="store_true")
    parser.add_argument("--impact", action="store_true")
    parser.add_argument("--projects", action="store_true")
    parser.add_argument("--snapshot", action="store_true")
    args = parser.parse_args()
    service = PlatformService()
    if args.recon:
        payload = service.recon()
    elif args.projects:
        payload = service.project_validate()
    elif args.snapshot:
        payload = service.snapshot()
    elif not args.query:
        parser.error("--query is required unless --recon, --projects or --snapshot is used")
    elif args.impact:
        payload = service.impact(args.query)
    elif args.horizontal:
        payload = service.horizontal(args.query)
    elif args.vertical:
        payload = service.vertical(args.query)
    else:
        payload = service.search(args.query)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
