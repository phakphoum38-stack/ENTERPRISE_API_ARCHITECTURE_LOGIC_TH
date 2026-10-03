#!/usr/bin/env python3
"""Build a source-SHA-pinned searchable M.2 inventory and relationship graph."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

try:
    from research_os_test_case_inventory import discover as discover_test_cases
except ModuleNotFoundError:
    from tools.research_os_test_case_inventory import discover as discover_test_cases


ROOT = Path(__file__).resolve().parents[1]

EXCLUDES = {
    ".git",
    ".dart_tool",
    "build",
    "dist",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".research_os_data",
    "m2_audit_index.json",
    "m2_audit_index_summary.txt",
}

M2_STATE_DIR_NAME = "m2"
M2_STATE_FILE_NAME = "audit_snapshot_state.json"
M2_STATE_SCHEMA = "RESEARCH_OS_M2_AUDIT_SNAPSHOT_V2"

TEXT_SUFFIXES = {
    ".py",
    ".dart",
    ".json",
    ".yml",
    ".yaml",
    ".md",
    ".txt",
    ".ps1",
    ".sh",
    ".toml",
    ".html",
    ".css",
    ".js",
    ".cs",
    ".cpp",
    ".h",
}

CONTRACT_RE = re.compile(r"current/[A-Z0-9_./-]+\.(?:json|ya?ml)")
INV_RE = re.compile(r"\bINV-\d{3}\b")

CAPABILITY_RULES = [
    ("final_gate", ("final_gate", "final-gate", "release_spine")),
    ("evidence", ("evidence", "provenance", "lineage")),
    ("authorization", ("authorization", "auth", "entitlement", "owner")),
    ("workflow", ("workflow", "orchestrat", "queue", "runner")),
    ("project_scale", ("100_project", "project_scale", "scale_execution")),
    ("schedule", ("schedule", "scheduler", "reconciliation")),
    ("control_center", ("control_center", "control-center")),
    ("surface", ("surface", "navigation", "flutter", "ios", "windows", "web")),
    ("assurance", ("aeos", "assurance", "invariant")),
    ("release", ("release", "artifact", "installer", "distribution")),
]

SEMANTIC_ASSURANCE_RELATIONS = frozenset(
    {
        "VERIFIED_BY",
        "ENFORCED_BY",
        "DISPATCHED_BY",
        "SUPPORTED_BY",
        "BOUND_TO",
    }
)


def git_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def data_root() -> Path:
    configured = os.getenv("RESEARCH_OS_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return (ROOT / ".research_os_data").resolve()


def m2_state_path() -> Path:
    return data_root() / M2_STATE_DIR_NAME / M2_STATE_FILE_NAME


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files() -> list[Path]:
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file()
        and not any(part in EXCLUDES for part in path.parts)
    )


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def load_snapshot_state() -> dict:
    path = m2_state_path()

    if not path.exists():
        return {
            "schema": M2_STATE_SCHEMA,
            "files": {},
        }

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return {
            "schema": M2_STATE_SCHEMA,
            "files": {},
        }

    if (
        payload.get("schema") != M2_STATE_SCHEMA
        or not isinstance(payload.get("files"), dict)
    ):
        return {
            "schema": M2_STATE_SCHEMA,
            "files": {},
        }

    return payload


def save_snapshot_state(source: str, rows: list[dict]) -> Path:
    path = m2_state_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema": M2_STATE_SCHEMA,
        "source_sha": source,
        "root": str(ROOT),
        "files": {
            row["path"]: row
            for row in rows
        },
    }

    temp = path.with_suffix(".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)

    return path


def contract_stem(path: str) -> str:
    """Return the canonical semantic stem for a contract path."""
    stem = Path(path).stem.lower()

    for suffix in ("_contract", "-contract"):
        if stem.endswith(suffix):
            stem = stem[: -len(suffix)]
            break

    return stem


def kind(path: str, required_contracts: tuple[str, ...] | list[str] = ()) -> str:
    if path.startswith(".github/workflows/"):
        return "workflow"

    if (
        "/test" in path
        or path.startswith("tests/")
        or Path(path).name.startswith("test_")
        or "_test." in path
    ):
        return "test"

    if path.startswith("docs/") or path.endswith((".md", ".txt")):
        return "documentation"

    if path.startswith("scripts/"):
        return "script"

    if path.endswith((".py", ".dart", ".ps1", ".sh", ".cs", ".cpp", ".h")):
        return "implementation"

    name = Path(path).name.upper()

    if Path(path).suffix.lower() == ".diff":
        return "other"

    if path in required_contracts:
        return "contract"

    if "CONTRACT" in name or path.startswith("current/CONTRACTS/"):
        return "contract"

    return "other"


def read_text(path: Path) -> str:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return ""

    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def capabilities(path: str, text: str) -> list[str]:
    hay = (path + " " + text[:12000]).lower()

    found = [
        name
        for name, needles in CAPABILITY_RULES
        if any(needle in hay for needle in needles)
    ]

    return found or ["general"]


def nid(kind_name: str, path: str) -> str:
    return f"{kind_name.upper()}:{path}"


def _declared_identities(path: str, text: str) -> set[str]:
    """Extract conservative canonical identities from artifact metadata."""
    values = {contract_stem(path)}

    patterns = (
        r'"(?:contract|contract_id|capability_id|component_id)"\s*:\s*"([A-Za-z0-9_.:/-]+)"',
        r'^(?:contract|contract_id|capability_id|component_id):\s*([A-Za-z0-9_.:/-]+)',
    )

    for pattern in patterns:
        values.update(
            value.lower()
            for value in re.findall(pattern, text, re.MULTILINE)
        )

    return {
        value
        for value in values
        if value
    }


def resolve_semantic_bindings(
    contract: str,
    rows: list[dict],
    by_path: dict[str, Path],
    contracts: list[str],
    implementations: list[str],
    workflows: list[str],
    tests: list[str],
) -> dict:
    """Resolve assurance bindings generically; ambiguity is never auto-selected."""
    del contracts

    contract_text = read_text(by_path[contract])
    bindings: list[tuple[str, str, str]] = []

    for row in rows:
        target = row["path"]

        if target == contract:
            continue

        if row["kind"] == "contract" and contract in row["contract_refs"]:
            bindings.append(
                (
                    "BOUND_TO",
                    target,
                    "explicit_contract_reference",
                )
            )

        elif row["kind"] in {"implementation", "workflow"}:
            if contract in row["contract_refs"]:
                relation = (
                    "ENFORCED_BY"
                    if row["kind"] == "implementation"
                    else "DISPATCHED_BY"
                )

                bindings.append(
                    (
                        relation,
                        target,
                        "explicit_contract_reference",
                    )
                )

    for target in tests:
        target_text = read_text(by_path[target])

        if (
            contract in target_text
            or Path(contract).name in target_text
            or contract_stem(contract) in Path(target).stem.lower()
        ):
            bindings.append(
                (
                    "VERIFIED_BY",
                    target,
                    "test_identity",
                )
            )

    for target in by_path:
        if target.startswith("evidence/") and contract in read_text(by_path[target]):
            bindings.append(
                (
                    "SUPPORTED_BY",
                    target,
                    "explicit_contract_reference",
                )
            )

    # Semantic fallback is deliberately unique.
    # Zero candidates remain unresolved.
    # Multiple candidates are ambiguous and must fail closed.
    identities = _declared_identities(contract, contract_text)

    for kind_name, candidates, relation in (
        ("implementation", implementations, "ENFORCED_BY"),
        ("workflow", workflows, "DISPATCHED_BY"),
    ):
        semantic = [
            candidate
            for candidate in candidates
            if identities
            & _declared_identities(
                candidate,
                read_text(by_path[candidate]),
            )
        ]

        if len(semantic) == 1:
            bindings.append(
                (
                    relation,
                    semantic[0],
                    "unique_semantic_identity",
                )
            )

        elif len(semantic) > 1:
            return {
                "bindings": sorted(set(bindings)),
                "unresolved": False,
                "ambiguous": True,
                "ambiguous_targets": sorted(semantic),
            }

    return {
        "bindings": sorted(set(bindings)),
        "unresolved": not bindings,
        "ambiguous": False,
        "ambiguous_targets": [],
    }


def required_authority_paths(by_path: dict[str, Path]) -> tuple[list[str], list[str]]:
    gate_path = "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"

    if gate_path not in by_path:
        return [], []

    text = read_text(by_path[gate_path])

    def section(name: str) -> list[str]:
        match = re.search(
            rf"^{name}:\n((?:  - .+\n)+)",
            text,
            re.MULTILINE,
        )

        if not match:
            return []

        return [
            line[4:].strip()
            for line in match.group(1).splitlines()
        ]

    return (
        section("required_contracts"),
        section("required_workflows"),
    )


def contract_test_matches(
    contract: str,
    test: str,
    by_path: dict[str, Path],
) -> bool:
    """Return True for explicit or strong semantic contract/test binding."""
    text = read_text(by_path[test])
    contract_path = Path(contract)
    stem = contract_stem(contract)
    test_stem = Path(test).stem.lower()

    if contract in text or contract_path.name in text:
        return True

    if stem and stem in test_stem:
        return True

    return False


def build_index() -> dict:
    source = git_sha()
    paths = files()
    by_path = {
        rel(path): path
        for path in paths
    }

    test_case_inventory = discover_test_cases()

    required_contracts, required_workflows = required_authority_paths(by_path)

    snapshot = load_snapshot_state()
    previous = snapshot.get("files", {})
    current_paths = {
        rel(path)
        for path in paths
    }

    rows: list[dict] = []

    for path_obj in paths:
        path = rel(path_obj)
        stat = path_obj.stat()
        old = previous.get(path)
        unchanged = False

        if old:
            unchanged = (
                old.get("size") == stat.st_size
                and old.get("mtime_ns") == stat.st_mtime_ns
                and isinstance(old.get("sha256"), str)
                and len(old.get("sha256", "")) == 64
            )

        if unchanged:
            row = dict(old)

        else:
            text = read_text(path_obj)
            digest = file_sha256(path_obj)

            if old and old.get("sha256") == digest:
                row = dict(old)
                row["size"] = stat.st_size
                row["mtime_ns"] = stat.st_mtime_ns
                row["sha256"] = digest

            else:
                row = {
                    "path": path,
                    "kind": kind(path, required_contracts),
                    "size": stat.st_size,
                    "mtime_ns": stat.st_mtime_ns,
                    "sha256": digest,
                    "capabilities": capabilities(path, text),
                    "contract_refs": sorted(
                        {
                            value
                            for value in CONTRACT_RE.findall(text)
                            if value in by_path
                        }
                    ),
                    "invariant_refs": sorted(
                        set(INV_RE.findall(text))
                    ),
                    "has_contract_reference": bool(
                        CONTRACT_RE.search(text)
                    ),
                    "has_test_reference": bool(
                        re.search(r"(?:test_|_test\.)", text)
                    ),
                    "has_workflow_reference": (
                        ".github/workflows/" in text
                    ),
                    "has_evidence_reference": bool(
                        re.search(
                            r"evidence|provenance|lineage",
                            text,
                            re.I,
                        )
                    ),
                    "has_final_gate_reference": bool(
                        re.search(
                            r"final[_ -]?gate|release_authority",
                            text,
                            re.I,
                        )
                    ),
                }

        rows.append(row)

    contracts = [
        row["path"]
        for row in rows
        if row["kind"] == "contract"
    ]

    tests = [
        row["path"]
        for row in rows
        if row["kind"] == "test"
    ]

    workflows = [
        row["path"]
        for row in rows
        if row["kind"] == "workflow"
    ]

    implementations = [
        row["path"]
        for row in rows
        if row["kind"] == "implementation"
    ]

    nodes: list[dict] = []
    node_ids: set[str] = set()
    edges: list[dict] = []

    def add_node(
        node_id: str,
        node_kind: str,
        path: str | None = None,
        state: str = "UNKNOWN",
    ) -> None:
        if node_id not in node_ids:
            node_ids.add(node_id)
            nodes.append(
                {
                    "id": node_id,
                    "kind": node_kind,
                    "path": path,
                    "state": state,
                }
            )

    contract_set = set(contracts)

    # Inventory-backed nodes and explicit references.
    for row in rows:
        row_kind = row["kind"].upper()
        row_path = row["path"]

        add_node(
            nid(row_kind, row_path),
            row_kind,
            row_path,
        )

        for contract in row["contract_refs"]:
            # Only authoritative inventory entries may become
            # CONTRACT nodes.
            if contract not in contract_set:
                continue

            add_node(
                nid("CONTRACT", contract),
                "CONTRACT",
                contract,
            )

            edges.append(
                {
                    "from": nid(row_kind, row_path),
                    "relation": "REFERENCES",
                    "to": nid("CONTRACT", contract),
                }
            )

            # Existing explicit references are also semantic assurance
            # evidence when the referencing artifact has an assurance role.
            if row_kind == "IMPLEMENTATION":
                edges.append(
                    {
                        "from": nid("CONTRACT", contract),
                        "relation": "ENFORCED_BY",
                        "to": nid(row_kind, row_path),
                    }
                )

            elif row_kind == "WORKFLOW":
                edges.append(
                    {
                        "from": nid("CONTRACT", contract),
                        "relation": "DISPATCHED_BY",
                        "to": nid(row_kind, row_path),
                    }
                )

            elif row_path.startswith("evidence/") or row_path.startswith(
                "evidence\\"
            ):
                edges.append(
                    {
                        "from": nid("CONTRACT", contract),
                        "relation": "SUPPORTED_BY",
                        "to": nid(row_kind, row_path),
                    }
                )

        for invariant in row["invariant_refs"]:
            add_node(
                f"INVARIANT:{invariant}",
                "INVARIANT",
                invariant,
            )

            edges.append(
                {
                    "from": nid(row_kind, row_path),
                    "relation": "ENFORCES_OR_REFERENCES",
                    "to": f"INVARIANT:{invariant}",
                }
            )

    # Explicit contract/test relationships.
    for contract in contracts:
        for test in tests:
            if contract_test_matches(contract, test, by_path):
                edges.append(
                    {
                        "from": nid("CONTRACT", contract),
                        "relation": "VERIFIED_BY",
                        "to": nid("TEST", test),
                    }
                )

    # Semantic contract bindings.
    semantic_results: dict[str, dict] = {}

    for contract in contracts:
        result = resolve_semantic_bindings(
            contract=contract,
            rows=rows,
            by_path=by_path,
            contracts=contracts,
            implementations=implementations,
            workflows=workflows,
            tests=tests,
        )

        semantic_results[contract] = result

        if result["ambiguous"]:
            continue

        for relation, target, reason in result["bindings"]:
            source_id = nid("CONTRACT", contract)

            if relation == "VERIFIED_BY":
                target_id = nid("TEST", target)
            elif relation == "ENFORCED_BY":
                target_id = nid("IMPLEMENTATION", target)
            elif relation == "DISPATCHED_BY":
                target_id = nid("WORKFLOW", target)
            elif relation == "SUPPORTED_BY":
                target_id = nid(
                    kind(
                        target,
                        required_contracts,
                    ),
                    target,
                )
            elif relation == "BOUND_TO":
                target_id = nid("CONTRACT", target)
            else:
                continue

            if target_id not in node_ids:
                continue

            edges.append(
                {
                    "from": source_id,
                    "relation": relation,
                    "to": target_id,
                    "reason": reason,
                }
            )

    # Workflow-to-workflow references.
    workflow_names = {
        Path(workflow).name: workflow
        for workflow in workflows
    }

    for workflow in workflows:
        text = read_text(by_path[workflow])

        for name, target in workflow_names.items():
            if target == workflow:
                continue

            if name in text:
                edges.append(
                    {
                        "from": nid("WORKFLOW", workflow),
                        "relation": "DISPATCHES_OR_REFERENCES",
                        "to": nid("WORKFLOW", target),
                    }
                )

    # FINAL_GATE remains the sole authority node.
    final_gate_path = "current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml"
    final_gate_exists = final_gate_path in by_path

    if final_gate_exists:
        add_node(
            "FINAL_GATE:UNIFIED",
            "AUTHORITY",
            final_gate_path,
            "VERIFIED",
        )

    for row in rows:
        if (
            row["has_final_gate_reference"]
            and row["kind"] != "workflow"
        ):
            edges.append(
                {
                    "from": nid(row["kind"], row["path"]),
                    "relation": "BINDS_TO",
                    "to": "FINAL_GATE:UNIFIED",
                }
            )

            if row["kind"] == "contract":
                edges.append(
                    {
                        "from": nid("CONTRACT", row["path"]),
                        "relation": "BOUND_TO",
                        "to": "FINAL_GATE:UNIFIED",
                    }
                )

    for workflow in workflows:
        if (
            "unified-final-gate" in workflow
            or "RESEARCH_OS_UNIFIED_FINAL_GATE"
            in read_text(by_path[workflow])
        ):
            edges.append(
                {
                    "from": nid("WORKFLOW", workflow),
                    "relation": "PARTICIPATES_IN",
                    "to": "FINAL_GATE:UNIFIED",
                }
            )

    # Deduplicate edges deterministically.
    deduped_edges: dict[tuple[str, str, str], dict] = {}

    for edge in edges:
        key = (
            edge["from"],
            edge["relation"],
            edge["to"],
        )

        if key not in deduped_edges:
            deduped_edges[key] = edge

    edges = sorted(
        deduped_edges.values(),
        key=lambda edge: (
            edge["from"],
            edge["relation"],
            edge["to"],
        ),
    )

    targets = {
        node["id"]
        for node in nodes
    }

    dangling = [
        edge
        for edge in edges
        if (
            edge["from"] not in targets
            or edge["to"] not in targets
        )
    ]

    findings: list[dict] = []

    # Required FINAL_GATE inventory.
    for required in required_contracts:
        if (
            required not in by_path
            or required not in contracts
        ):
            findings.append(
                {
                    "state": "MISSING",
                    "code": (
                        "REQUIRED_FINAL_GATE_CONTRACT_"
                        "MISSING_FROM_M2"
                    ),
                    "path": required,
                }
            )

    for required in required_workflows:
        if (
            required not in by_path
            or required not in workflows
        ):
            findings.append(
                {
                    "state": "MISSING",
                    "code": (
                        "REQUIRED_FINAL_GATE_WORKFLOW_"
                        "MISSING_FROM_M2"
                    ),
                    "path": required,
                }
            )

    # Semantic binding findings.
    for contract, result in semantic_results.items():
        if result["ambiguous"]:
            findings.append(
                {
                    "state": "AMBIGUOUS",
                    "code": "CONTRACT_SEMANTIC_BINDING_AMBIGUOUS",
                    "path": contract,
                    "targets": result["ambiguous_targets"],
                }
            )

        elif result["unresolved"]:
            findings.append(
                {
                    "state": "UNRESOLVED",
                    "code": "CONTRACT_SEMANTIC_BINDING_UNRESOLVED",
                    "path": contract,
                }
            )

    # Every contract should have either explicit test assurance
    # or another assurance binding.
    for contract in contracts:
        verified = any(
            contract_test_matches(
                contract,
                test,
                by_path,
            )
            for test in tests
        )

        has_assurance = any(
            edge["from"] == nid("CONTRACT", contract)
            and edge["relation"] in SEMANTIC_ASSURANCE_RELATIONS
            for edge in edges
        )

        semantic = semantic_results.get(
            contract,
            {
                "ambiguous": False,
                "unresolved": True,
            },
        )

        if not verified and not has_assurance:
            findings.append(
                {
                    "state": "INCOMPLETE",
                    "code": "CONTRACT_WITHOUT_ASSURANCE_BINDING",
                    "path": contract,
                }
            )

        if semantic["ambiguous"]:
            # Ambiguity is already represented as its own finding.
            # Do not silently convert it into a selected binding.
            continue

    integrity = {
        "exact_source_sha": bool(
            re.fullmatch(
                r"[0-9a-f]{40}",
                source,
            )
        ),
        "inventory_completeness": bool(rows),
        "test_case_inventory": (
            test_case_inventory["source_sha"] == source
            and test_case_inventory["inventory"]["test_files"] > 0
            and test_case_inventory["inventory"]["discovered_test_cases"] > 0
        ),
        "duplicate_path_detection": (
            len({row["path"] for row in rows}) == len(rows)
        ),
        "unique_node_ids": (
            len(node_ids) == len(nodes)
        ),
        "no_dangling_edges": not dangling,
        "contract_test_linkage": (
            bool(contracts)
            and any(
                edge["from"].startswith("CONTRACT:")
                and edge["relation"] == "VERIFIED_BY"
                and edge["to"].startswith("TEST:")
                for edge in edges
            )
            and all(
                any(
                    edge["from"] == nid("CONTRACT", contract)
                    and edge["relation"] == "VERIFIED_BY"
                    for edge in edges
                )
                for contract in contracts
                if any(
                    contract_test_matches(
                        contract,
                        test,
                        by_path,
                    )
                    for test in tests
                )
            )
        ),
        "contract_nodes_are_inventory_backed": all(
            node["id"] == nid("CONTRACT", node["path"])
            and node["path"] in contract_set
            for node in nodes
            if node["kind"] == "CONTRACT"
        ),
        "semantic_assurance_graph": any(
            edge["relation"] in SEMANTIC_ASSURANCE_RELATIONS
            for edge in edges
        ),
        "contract_implementation_linkage": (
            bool(implementations)
            and any(
                edge["from"].startswith("IMPLEMENTATION:")
                and edge["relation"] == "REFERENCES"
                and edge["to"].startswith("CONTRACT:")
                for edge in edges
            )
            and all(
                any(
                    edge["from"] == nid(
                        "IMPLEMENTATION",
                        implementation,
                    )
                    and edge["relation"] == "REFERENCES"
                    and edge["to"].startswith("CONTRACT:")
                    for edge in edges
                )
                for implementation in implementations
                if any(
                    contract in read_text(by_path[implementation])
                    for contract in contracts
                )
            )
        ),
        "semantic_binding_integrity": all(
            not result["ambiguous"]
            for result in semantic_results.values()
        ),
        "workflow_inventory": bool(workflows),
        "contract_inventory": bool(contracts),
        "required_contract_inventory": (
            bool(required_contracts)
            and all(
                path in contracts
                for path in required_contracts
            )
        ),
        "required_workflow_inventory": (
            bool(required_workflows)
            and all(
                path in workflows
                for path in required_workflows
            )
        ),
        "invariant_inventory": any(
            row["invariant_refs"]
            for row in rows
        ),
        "final_gate_node": (
            final_gate_exists
            and "FINAL_GATE:UNIFIED" in targets
        ),
    }

    save_snapshot_state(
        source,
        rows,
    )

    return {
        "schema": "RESEARCH_OS_M2_AUDIT_GRAPH_V2",
        "source_sha": source,
        "root": str(ROOT),
        "inventory": {
            "files": len(rows),
            "contracts": len(contracts),
            "implementations": len(implementations),
            "tests": len(tests),
            "workflows": len(workflows),
            "required_contracts": len(required_contracts),
            "required_workflows": len(required_workflows),
            "test_case_inventory": test_case_inventory["inventory"],
            "nodes": len(nodes),
            "edges": len(edges),
            "findings": len(findings),
        },
        "integrity": integrity,
        "findings": findings,
        "semantic_results": semantic_results,
        "nodes": nodes,
        "edges": edges,
        "files": rows,
        "dangling_edges": dangling,
        "incremental": {
            "state_path": str(m2_state_path()),
            "previous_files": len(previous),
            "current_files": len(current_paths),
            "reused_files": sum(
                1
                for row in rows
                if (
                    row["path"] in previous
                    and previous[row["path"]].get("size")
                    == row.get("size")
                    and previous[row["path"]].get("mtime_ns")
                    == row.get("mtime_ns")
                )
            ),
            "deleted_files": sorted(
                set(previous) - current_paths
            ),
        },
    }


def build_graph() -> dict:
    return build_index()


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--output",
        default="m2_audit_index.json",
    )

    parser.add_argument(
        "--summary",
        default="m2_audit_index_summary.txt",
    )

    parser.add_argument(
        "--query",
        default="",
    )

    args = parser.parse_args()

    graph = build_index()

    if not all(graph["integrity"].values()):
        print("M2_AUDIT_INDEX=FAIL")

        for key, value in graph["integrity"].items():
            if not value:
                print(f"INTEGRITY_FAIL={key}")

        return 2

    if args.query:
        query = args.query.lower()

        nodes = [
            node
            for node in graph["nodes"]
            if (
                query in node["id"].lower()
                or query in (node.get("path") or "").lower()
            )
        ]

        edges = [
            edge
            for edge in graph["edges"]
            if query in json.dumps(edge).lower()
        ]

        print(
            json.dumps(
                {
                    "query": args.query,
                    "nodes": nodes,
                    "edges": edges,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

        return 0

    Path(args.output).write_text(
        json.dumps(
            graph,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    summary = [
        "RESEARCH OS M.2 WHOLE-SYSTEM AUDIT GRAPH",
        f"SOURCE_SHA={graph['source_sha']}",
        *[
            f"{key.upper()}={value}"
            for key, value in graph["inventory"].items()
        ],
        "M2_AUDIT_GRAPH=PASS",
        "M2_AUDIT_INDEX=PASS",
    ]

    Path(args.summary).write_text(
        "\n".join(summary) + "\n",
        encoding="utf-8",
    )

    print("\n".join(summary))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
 
