#!/usr/bin/env python3
"""Independent, read-only verifier for AEOS squash reconciliation evidence.

This verifier intentionally does not import or delegate to the source-stage
validator. It recomputes the BASE->HEAD and BASE->MERGE facts directly from
Git objects and emits an independent verification result as an artifact.

It never mutates the reconciliation manifest and never grants merge authority.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "current" / "AEOS_SQUASH_RECONCILIATIONS.json"
OUTPUT = REPO / "independent-forensic-verification.json"

EXPECTED_DIVERGENT = {
    "owner_special/flutter_app/test/team_acl_test.dart",
    "owner_special/team_center_contract.json",
    "owner_special/tests/test_port_topology_contract.py",
}
EXPECTED_ACCEPTED = {
    "current/AEOS_HOLD_RECOVERY_CONTRACT.json",
    "owner_special/research_os_friend/hold_recovery_engine.py",
    "owner_special/tests/test_hold_recovery_engine.py",
}
EXPECTED_PORTS = {"8787", "8788", "8790"}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def paths(a: str, b: str) -> set[str]:
    raw = git("diff", "--name-only", a, b)
    return {line for line in raw.splitlines() if line}


def patch(a: str, b: str, path: str) -> bytes:
    return git_bytes("diff", "--no-ext-diff", "--binary", a, b, "--", path)


def file_at(commit: str, path: str) -> bytes:
    return git_bytes("show", f"{commit}:{path}")


def exists_at(commit: str, path: str) -> bool:
    return subprocess.run(
        ["git", "cat-file", "-e", f"{commit}:{path}"],
        cwd=REPO,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0


def fail(reason: str) -> int:
    result = {
        "schema": "aeos.squash-reconciliation.independent-forensic.v1",
        "status": "FAIL",
        "reason": reason,
        "merge_authority": False,
        "self_certification": False,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 1


def parse_acl_services(content: bytes) -> set[str]:
    text = content.decode("utf-8")
    match = re.search(r'"services"\s*:\s*\{(?P<body>.*?)\n\s*\}\s*\n\s*\}', text, re.DOTALL)
    if not match:
        raise ValueError("ACL services object not found")
    return set(re.findall(r'"(\d{4})"\s*:', match.group("body")))


def parse_team_services(content: bytes) -> set[int]:
    data = json.loads(content.decode("utf-8"))
    return set(data["owner"]["services"])


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))

    # The independent verifier must not consume a self-promoted status.
    if data.get("independent_forensic_status") != "PENDING":
        return fail("manifest independent_forensic_status must remain PENDING")
    if data.get("merge_authority") is not False:
        return fail("manifest merge_authority must remain false")
    if data.get("self_certification") is not False:
        return fail("manifest self_certification must remain false")

    base = data["base_sha"]
    head = data["head_sha"]
    merge = data["merge_sha"]

    try:
        if git("rev-parse", base) != base:
            return fail("BASE SHA does not resolve exactly")
        if git("rev-parse", head) != head:
            return fail("HEAD SHA does not resolve exactly")
        if git("rev-parse", merge) != merge:
            return fail("MERGE SHA does not resolve exactly")
    except subprocess.CalledProcessError as exc:
        return fail(f"git identity resolution failed: {exc}")

    parents = git("rev-list", "--parents", "-n", "1", merge).split()[1:]
    if parents != [base]:
        return fail("MERGE must have exactly BASE as its only parent")
    if git("merge-base", base, merge) != base:
        return fail("BASE is not the merge-base of BASE and MERGE")

    head_paths = paths(base, head)
    merge_paths = paths(base, merge)
    divergent = {
        p for p in head_paths | merge_paths if patch(base, head, p) != patch(base, merge, p)
    }
    if divergent != EXPECTED_DIVERGENT:
        return fail(f"divergent inventory mismatch: {sorted(divergent)}")
    if set(data.get("divergent_paths", [])) != divergent:
        return fail("manifest divergent_paths do not match independently derived paths")

    accepted = merge_paths
    if accepted != EXPECTED_ACCEPTED:
        return fail(f"accepted payload mismatch: {sorted(accepted)}")
    if set(data.get("accepted_payload_paths", [])) != accepted:
        return fail("manifest accepted_payload_paths do not match BASE->MERGE")
    if data.get("accepted_payload_digest") != merge:
        return fail("accepted payload digest is not the exact MERGE SHA")

    evidence = data.get("canonical_conflict_evidence", {})
    if set(evidence) != divergent:
        return fail("canonical conflict evidence does not cover exactly all divergent paths")
    for p in divergent:
        item = evidence[p]
        if item.get("stale_or_conflicting") is not True or not item.get("evidence"):
            return fail(f"missing stale/conflict evidence for {p}")

    # Independent semantic spot-checks for the known historical divergence.
    acl = parse_acl_services(file_at(head, "owner_special/flutter_app/test/team_acl_test.dart"))
    acl_base = parse_acl_services(file_at(base, "owner_special/flutter_app/test/team_acl_test.dart"))
    acl_merge = parse_acl_services(file_at(merge, "owner_special/flutter_app/test/team_acl_test.dart"))
    if acl != EXPECTED_PORTS | {"8789"} or acl_base != EXPECTED_PORTS or acl_merge != EXPECTED_PORTS:
        return fail(f"ACL topology divergence does not match the declared stale 8789 evidence: head={sorted(acl)}, base={sorted(acl_base)}, merge={sorted(acl_merge)}")

    team = parse_team_services(file_at(head, "owner_special/team_center_contract.json"))
    team_base = parse_team_services(file_at(base, "owner_special/team_center_contract.json"))
    team_merge = parse_team_services(file_at(merge, "owner_special/team_center_contract.json"))
    expected_int_ports = {8787, 8788, 8790}
    if team != expected_int_ports | {8789} or team_base != expected_int_ports or team_merge != expected_int_ports:
        return fail(f"Team Center divergence does not match the declared stale 8789 evidence: head={sorted(team)}, base={sorted(team_base)}, merge={sorted(team_merge)}")

    # The topology test is historical lineage evidence, not BASE->MERGE payload.
    # BASE and MERGE contain the canonical test; the stale #366 HEAD does not.
    topo = "owner_special/tests/test_port_topology_contract.py"
    if not exists_at(base, topo) or not exists_at(merge, topo) or exists_at(head, topo):
        return fail("topology contract historical divergence does not match BASE/MERGE lineage")

    result = {
        "schema": "aeos.squash-reconciliation.independent-forensic.v1",
        "status": "VERIFIED",
        "verification_mode": "independent_git_object_reproduction",
        "target_pr": data["pr_number"],
        "base_sha": base,
        "head_sha": head,
        "merge_sha": merge,
        "merge_parent_sha": base,
        "divergent_paths": sorted(divergent),
        "accepted_payload_paths": sorted(accepted),
        "accepted_payload_digest": merge,
        "semantic_checks": {
            "acl_8789_stale_in_head_only": True,
            "team_center_8789_stale_in_head_only": True,
            "canonical_topology_test_in_base_and_merge": True,
            "topology_test_absent_from_head": True,
        },
        "manifest_status_consumed": "PENDING",
        "merge_authority": False,
        "self_certification": False,
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
