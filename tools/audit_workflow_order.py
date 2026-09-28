#!/usr/bin/env python3
"""Static audit of GitHub Actions order, dependencies, SHA and release lineage."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
REPORTS = ROOT / "reports"
SPINE = ["SOURCE", "QUALITY", "BUILD", "IDENTITY", "PACKAGE", "INSTALL_E2E", "PROVENANCE", "LINEAGE", "CANDIDATE", "CERTIFICATION", "RELEASE"]
PROTECTED = {"TARGET_SHA", "OWNER_BUILD_IDENTITY", "SHA256", "INSTALLED_PROVENANCE", "CANONICAL_LINEAGE", "RELEASE_CERTIFICATION"}


def read_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError(f"workflow root is not a mapping: {path}")
    return data


def classify(name: str, text: str) -> str:
    s = f"{name} {text}".lower()
    rules = [
        ("CERTIFICATION", ["final-gate", "certification"]),
        ("RELEASE", ["release"]),
        ("PROVENANCE", ["provenance", "installed-owner"]),
        ("IDENTITY", ["identity-gate", "build identity", "branding-gate"]),
        ("INSTALL_E2E", ["installer", "install e2e", "clean install"]),
        ("CANDIDATE", ["candidate"]),
        ("LINEAGE", ["lineage"]),
        ("PACKAGE", ["package", "artifact"]),
        ("BUILD", ["build", "flutter build", "publish"]),
        ("QUALITY", ["ci", "test", "lint", "analy", "performance", "validation", "gate"]),
    ]
    for stage, needles in rules:
        if any(n in s for n in needles):
            return stage
    return "UTILITY"


def workflow_run_edges(data: dict[str, Any]) -> list[str]:
    on = data.get("on", data.get(True, {})) or {}
    wr = on.get("workflow_run") if isinstance(on, dict) else None
    if not wr:
        return []
    if isinstance(wr, dict):
        names = wr.get("workflows", [])
        return names if isinstance(names, list) else [str(names)]
    return []


def extract_dispatch_targets(text: str, known: set[str]) -> list[str]:
    out: set[str] = set()
    for match in re.findall(r"[A-Za-z0-9_.-]+\.ya?ml", text):
        if match in known:
            out.add(match)
    return sorted(out)


def scan_workflows() -> tuple[dict[str, Any], list[dict[str, str]], list[dict[str, str]], list[str]]:
    known = {p.name for p in WORKFLOWS.glob("*.y*ml")}
    records: dict[str, Any] = {}
    edges: list[dict[str, str]] = []
    artifact_edges: list[dict[str, str]] = []
    errors: list[str] = []
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        try:
            data = read_yaml(path)
        except Exception as exc:
            errors.append(f"{path.name}: YAML_PARSE_ERROR: {exc}")
            continue
        jobs = data.get("jobs") or {}
        if not isinstance(jobs, dict):
            errors.append(f"{path.name}: jobs is not a mapping")
            jobs = {}
        job_names = list(jobs)
        job_needs: dict[str, list[str]] = {}
        for job, spec in jobs.items():
            if not isinstance(spec, dict):
                continue
            needs = spec.get("needs", [])
            if isinstance(needs, str):
                needs = [needs]
            needs = needs if isinstance(needs, list) else []
            job_needs[job] = [str(x) for x in needs]
            for dep in job_needs[job]:
                if dep in jobs:
                    edges.append({"from": f"{path.name}:{dep}", "to": f"{path.name}:{job}", "type": "needs"})
            spec_text = json.dumps(spec, sort_keys=True, default=str)
            if "upload-artifact" in spec_text:
                artifact_edges.append({"workflow": path.name, "job": job, "type": "producer"})
            if "download-artifact" in spec_text:
                artifact_edges.append({"workflow": path.name, "job": job, "type": "consumer"})
        for target in extract_dispatch_targets(text, known):
            if target != path.name:
                edges.append({"from": path.name, "to": target, "type": "dispatch-text"})
        for target in workflow_run_edges(data):
            if target in known:
                edges.append({"from": target, "to": path.name, "type": "workflow_run"})
        target_sha = {
            "input": bool(re.search(r"target_sha", text, re.I)),
            "immutable_propagation": bool(re.search(r"inputs\.target_sha|TARGET_SHA", text)),
            "github_sha": bool(re.search(r"github\.sha|GITHUB_SHA", text)),
            "checkout_ref": bool(re.search(r"inputs\.target_sha|env\.TARGET_SHA", text)),
            "head_check": "git rev-parse HEAD" in text and "TARGET_SHA" in text,
        }
        records[path.name] = {
            "stage": classify(path.name, text),
            "jobs": job_names,
            "job_needs": job_needs,
            "workflow_run": workflow_run_edges(data),
            "dispatch_targets": extract_dispatch_targets(text, known),
            "target_sha": target_sha,
            "artifact_producer": any(e["workflow"] == path.name and e["type"] == "producer" for e in artifact_edges),
            "artifact_consumer": any(e["workflow"] == path.name and e["type"] == "consumer" for e in artifact_edges),
        }
    return records, edges, artifact_edges, errors


def detect_cycles(nodes: set[str], edges: list[dict[str, str]]) -> list[list[str]]:
    adj: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        adj[e["from"]].append(e["to"])
    color: dict[str, int] = defaultdict(int)
    stack: list[str] = []
    cycles: list[list[str]] = []
    def dfs(node: str) -> None:
        color[node] = 1
        stack.append(node)
        for nxt in adj[node]:
            if color[nxt] == 0:
                dfs(nxt)
            elif color[nxt] == 1 and nxt in stack:
                i = stack.index(nxt)
                cycles.append(stack[i:] + [nxt])
        stack.pop()
        color[node] = 2
    for node in sorted(nodes):
        if color[node] == 0:
            dfs(node)
    return cycles


def findings(records: dict[str, Any], edges: list[dict[str, str]], artifact_edges: list[dict[str, str]], parse_errors: list[str]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = [{"severity": "FAIL", "code": "YAML_PARSE_ERROR", "message": e} for e in parse_errors]
    for name, rec in records.items():
        sha = rec["target_sha"]
        stage = rec["stage"]
        if stage in {"BUILD", "IDENTITY", "PACKAGE", "INSTALL_E2E", "PROVENANCE", "LINEAGE", "CANDIDATE", "CERTIFICATION", "RELEASE"} and sha["github_sha"] and not sha["input"]:
            out.append({"severity": "WARN", "code": "IMPLICIT_GITHUB_SHA", "message": f"{name}: uses github.sha/GITHUB_SHA without target_sha input evidence"})
        if stage in {"BUILD", "IDENTITY", "PACKAGE", "PROVENANCE", "LINEAGE", "CANDIDATE", "CERTIFICATION", "RELEASE"} and sha["input"] and not sha["head_check"]:
            out.append({"severity": "WARN", "code": "MISSING_SHA_HEAD_CHECK", "message": f"{name}: target_sha is referenced but no explicit checkout HEAD equality check was detected"})
        if rec["workflow_run"] and not re.search(r"conclusion\s*==\s*['\"]success['\"]|conclusion\s*!=\s*['\"]success['\"]", WORKFLOWS.joinpath(name).read_text(encoding="utf-8"), re.I):
            out.append({"severity": "WARN", "code": "UNGUARDED_WORKFLOW_RUN", "message": f"{name}: workflow_run dependency has no obvious conclusion guard"})
    cycles = detect_cycles(set(records) | {e["from"] for e in edges} | {e["to"] for e in edges}, edges)
    for cycle in cycles:
        out.append({"severity": "FAIL", "code": "DEPENDENCY_CYCLE", "message": " -> ".join(cycle)})
    producers = [e["workflow"] for e in artifact_edges if e["type"] == "producer"]
    consumers = [e["workflow"] for e in artifact_edges if e["type"] == "consumer"]
    if consumers and not producers:
        out.append({"severity": "FAIL", "code": "ARTIFACT_WITHOUT_PRODUCER", "message": "artifact consumer detected but no producer was detected"})
    release = [n for n, r in records.items() if r["stage"] == "RELEASE"]
    if release:
        joined = " ".join(e["from"] + " " + e["to"] for e in edges)
        for required in ("candidate", "final-gate", "lineage", "provenance"):
            if required not in joined.lower():
                out.append({"severity": "WARN", "code": "RELEASE_SPINE_GAP", "message": f"release graph has no obvious edge containing {required}"})
    return out


def render_txt(records: dict[str, Any], edges: list[dict[str, str]], artifact_edges: list[dict[str, str]], issues: list[dict[str, str]], ref: str) -> str:
    counts: dict[str, int] = defaultdict(int)
    for r in records.values():
        counts[r["stage"]] += 1
    fail = sum(i["severity"] == "FAIL" for i in issues)
    warn = sum(i["severity"] == "WARN" for i in issues)
    lines = ["RESEARCH OS WORKFLOW INTELLIGENCE AUDIT", "=" * 72, f"Ref: {ref}", f"Workflows scanned: {len(records)}", f"FAIL: {fail} | WARN: {warn}", "", "STAGE INVENTORY", "-" * 72]
    for stage in SPINE + ["UTILITY"]:
        if counts.get(stage):
            lines.append(f"{stage:16} {counts[stage]}")
    lines += ["", "WORKFLOW MAP", "-" * 72]
    for name in sorted(records):
        lines.append(f"{name:50} [{records[name]['stage']}]")
    lines += ["", "DEPENDENCY EDGES", "-" * 72]
    for e in edges:
        lines.append(f"{e['from']} -> {e['to']} [{e['type']}]")
    lines += ["", "ARTIFACT SIGNALS", "-" * 72]
    for e in artifact_edges:
        lines.append(f"{e['workflow']}:{e['job']} [{e['type']}]")
    lines += ["", "FINDINGS", "-" * 72]
    if issues:
        for i in issues:
            lines.append(f"[{i['severity']}] {i['code']}: {i['message']}")
    else:
        lines.append("NONE")
    lines += ["", "CANONICAL RELEASE SPINE", "-" * 72, " -> ".join(SPINE), "", f"FINAL RESULT: {'FAIL' if fail else 'PASS WITH WARNINGS' if warn else 'PASS'}"]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ref", default="working-tree")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    if not WORKFLOWS.exists():
        print("workflow directory missing", file=sys.stderr)
        return 2
    records, edges, artifact_edges, parse_errors = scan_workflows()
    issues = findings(records, edges, artifact_edges, parse_errors)
    REPORTS.mkdir(exist_ok=True)
    graph = {"version": 1, "ref": args.ref, "release_spine": SPINE, "protected_gates": sorted(PROTECTED), "workflows": records, "edges": edges, "artifacts": artifact_edges, "findings": issues}
    (REPORTS / "WORKFLOW_DEPENDENCY_GRAPH.json").write_text(json.dumps(graph, indent=2, sort_keys=True), encoding="utf-8")
    txt = render_txt(records, edges, artifact_edges, issues, args.ref)
    (REPORTS / "WORKFLOW_BUILD_ORDER_AUDIT.txt").write_text(txt, encoding="utf-8")
    (REPORTS / "WORKFLOW_BUILD_ORDER.md").write_text("# Workflow Build Order Audit\n\n```text\n" + txt + "```\n", encoding="utf-8")
    print(txt, end="")
    return 1 if any(i["severity"] == "FAIL" for i in issues) or (args.strict and issues) else 0


if __name__ == "__main__":
    raise SystemExit(main())
