#!/usr/bin/env python3
"""Validate the canonical Platform runtime-resolution boundary."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current" / "RESEARCH_OS_PLATFORM_RUNTIME_RESOLUTION_CONTRACT.json"


def fail(message: str) -> None:
    raise SystemExit(f"PLATFORM_RUNTIME_RESOLUTION=FAIL: {message}")


def main() -> None:
    if not CONTRACT.is_file():
        fail("missing runtime-resolution contract")

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    required = {
        "contract_id": "research-os-platform-runtime-resolution-v1",
        "status": "ACTIVE",
    }
    for key, expected in required.items():
        if data.get(key) != expected:
            fail(f"{key} must be {expected!r}")

    flow = data.get("flow", [])
    expected_flow = [
        "SURFACE", "SURFACE_MATRIX", "CAPABILITY", "PATH_RESOLUTION",
        "RUNTIME_SELECTION", "RESOURCE_DISCOVERY", "EXECUTION_PLAN",
        "QUEUE", "STATELESS_RUNNER", "EVIDENCE",
    ]
    if flow != expected_flow:
        fail("canonical resolution flow drifted")

    matrix = data.get("surface_matrix", {})
    if matrix.get("source") != "docs/RESEARCH_OS_SYSTEM_PLATFORM_MATRIX.md":
        fail("Surface Matrix source is not canonical")
    if matrix.get("flutter_is_consumer") is not True:
        fail("Flutter must remain a Surface Matrix consumer")
    if matrix.get("flutter_is_not_source_of_truth") is not True:
        fail("Flutter must not become Platform source of truth")

    path = data.get("path_resolution", {})
    for key in (
        "must_be_contract_backed",
        "must_be_workspace_scoped",
        "must_reject_path_traversal",
        "must_reject_unknown_paths",
        "must_not_bypass_authorization",
        "must_not_execute",
    ):
        if path.get(key) is not True:
            fail(f"path-resolution invariant missing: {key}")

    runtime = data.get("runtime_selection", {})
    if runtime.get("canonical_runner") != "v3/research_os_v3/runner.py":
        fail("canonical runner drifted")
    if runtime.get("queue") != "v3/research_os_v3/queue.py":
        fail("canonical queue drifted")
    if runtime.get("worker_pool") != "v3/worker_pool.py":
        fail("canonical worker pool drifted")
    if runtime.get("engine_to_runner_direct_call_forbidden") is not True:
        fail("direct Engine-to-Runner invocation must remain forbidden")

    local = data.get("local_compute", {})
    if local.get("nvme") != "MEMORY_FABRIC_T2_STORAGE_BACKED":
        fail("NVMe tier identity drifted")
    if local.get("m2_role") != "DESCRIPTIVE_DISCOVERY_AND_AUDIT":
        fail("M.2 role drifted")
    if local.get("m2_is_authorization") is not False:
        fail("M.2 must not authorize")
    if local.get("m2_is_release_authority") is not False:
        fail("M.2 must not release")

    conflict = data.get("resource_conflict", {})
    for key, expected in {
        "policy": "REJECT",
        "stop_execution": True,
        "release_resources": True,
        "ack_or_reconcile_delivery": True,
        "same_version_overwrite": False,
        "alternate_version_branching_allowed": True,
    }.items():
        if conflict.get(key) != expected:
            fail(f"resource-conflict invariant drifted: {key}")

    for path in (
        "docs/RESEARCH_OS_SYSTEM_PLATFORM_MATRIX.md",
        "current/RESEARCH_OS_UNIVERSAL_RUNNER_CONTRACT.json",
        "current/RESEARCH_OS_MEMORY_FABRIC_CONTRACT.json",
        "v3/research_os_v3/runner.py",
        "v3/research_os_v3/queue.py",
        "v3/worker_pool.py",
    ):
        if not (ROOT / path).exists():
            fail(f"missing runtime-resolution anchor: {path}")

    print("PLATFORM_RUNTIME_RESOLUTION=PASS")
    print("SURFACE_MATRIX=CANONICAL")
    print("PATH_RESOLUTION=PLATFORM_OWNED")
    print("RUNTIME=EXISTING_SHARED_EXECUTION_PLANE")
    print("M2=DESCRIPTIVE_ONLY")
    print("RELEASE_AUTHORITY=FINAL_GATE")


if __name__ == "__main__":
    main()
