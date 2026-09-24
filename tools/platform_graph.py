#!/usr/bin/env python3
"""Bounded logical Platform Graph Engine.

This module provides one generic engine over the existing Platform contracts and
registries. It is descriptive/read-only: it never grants authority, mutates
runtime state, merges, approves, changes branch protection, or rewrites history.
The 10^10 target is logical coverage, not physical materialization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


RELATIONS = {
    "REQUIRES", "ENABLES", "BLOCKS", "CONFLICTS", "IMPACTS", "SUPERSEDES",
    "PRODUCES", "OBSERVES", "VERIFIES", "PROVES", "RECOVERS", "LEARNS_FROM",
    "EVOLVES_TO",
}
REALITY_STATES = {"CLAIMED", "OBSERVED", "MEASURED", "REPRODUCED", "VERIFIED", "CONTRADICTED", "UNKNOWN"}


@dataclass(frozen=True)
class Node:
    node_id: str
    kind: str
    state: str = "UNKNOWN"
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    source: str
    relation: str
    target: str
    attrs: dict[str, Any] = field(default_factory=dict)


class PlatformGraph:
    """Generic bounded graph over authoritative Research OS metadata."""

    def __init__(self, contract: dict[str, Any], registry: dict[str, Any]) -> None:
        self.contract = contract
        self.registry = registry
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self._load_registry()

    @classmethod
    def from_paths(cls, contract_path: str | Path, registry_path: str | Path) -> "PlatformGraph":
        contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
        registry = json.loads(Path(registry_path).read_text(encoding="utf-8"))
        return cls(contract, registry)

    def _load_registry(self) -> None:
        for record in self.registry.get("records", []):
            work_id = record.get("work_id")
            if not work_id:
                continue
            self.add_node(Node(work_id, "WORK", record.get("status", "UNKNOWN"), dict(record)))
            for dependency in record.get("dependencies", []):
                target = dependency if dependency in self.nodes else f"plane:{dependency}"
                if target not in self.nodes:
                    self.add_node(Node(target, "PLANE"))
                self.add_edge(Edge(work_id, "REQUIRES", target))

    def add_node(self, node: Node) -> None:
        if not node.node_id:
            raise ValueError("missing_node_id")
        if node.node_id in self.nodes:
            raise ValueError(f"duplicate_node_id:{node.node_id}")
        self.nodes[node.node_id] = node

    def add_edge(self, edge: Edge) -> None:
        if edge.relation not in RELATIONS:
            raise ValueError(f"invalid_relation:{edge.relation}")
        if not edge.source or not edge.target:
            raise ValueError("missing_edge_endpoint")
        self.edges.append(edge)

    def neighbors(self, node_id: str, relation: str | None = None) -> list[str]:
        return [
            e.target for e in self.edges
            if e.source == node_id and (relation is None or e.relation == relation)
        ]

    def trace(self, start: str, *, relation: str | None = None, depth: int = 10) -> list[str]:
        if start not in self.nodes:
            raise KeyError(f"unknown_node:{start}")
        if depth < 0:
            raise ValueError("depth_must_be_non_negative")
        seen = {start}
        frontier = [start]
        ordered = [start]
        for _ in range(depth):
            nxt: list[str] = []
            for node_id in frontier:
                for target in self.neighbors(node_id, relation):
                    if target not in seen:
                        seen.add(target)
                        nxt.append(target)
                        ordered.append(target)
            frontier = nxt
            if not frontier:
                break
        return ordered

    def find(self, *, kind: str | None = None, state: str | None = None,
             attribute: str | None = None, value: Any = None) -> list[Node]:
        result = []
        for node in self.nodes.values():
            if kind is not None and node.kind != kind:
                continue
            if state is not None and node.state != state:
                continue
            if attribute is not None and node.attrs.get(attribute) != value:
                continue
            result.append(node)
        return result

    def unknowns(self) -> list[Node]:
        return self.find(state="UNKNOWN") + [
            n for n in self.nodes.values() if n.attrs.get("resolution") == "UNKNOWN"
        ]

    def conflicts(self) -> list[Edge]:
        return [e for e in self.edges if e.relation == "CONFLICTS"]

    def validate(self) -> list[str]:
        failures: list[str] = []
        expected = self.contract.get("contract_id")
        if expected != "research-os-platform-virtual-workspace-v1":
            failures.append("contract_id")
        if self.registry.get("contract_ref") != "current/PLATFORM_VIRTUAL_WORKSPACE_CONTRACT.json":
            failures.append("registry_contract_ref")
        authority = self.contract.get("authority", {})
        if authority.get("descriptive_only") is not True:
            failures.append("authority_not_descriptive")
        for key in (
            "may_merge", "may_approve", "may_grant_permissions",
            "may_change_branch_protection", "may_rewrite_history",
        ):
            if authority.get(key) is not False:
                failures.append(f"authority:{key}")
        seen_paths: set[str] = set()
        for record in self.registry.get("records", []):
            work_id = record.get("work_id", "?")
            for field_name in self.contract.get("required_record_fields", []):
                if field_name not in record or record.get(field_name) is None:
                    failures.append(f"missing:{work_id}:{field_name}")
            path = record.get("virtual_path")
            if path in seen_paths:
                failures.append(f"duplicate_virtual_path:{path}")
            seen_paths.add(path)
            if record.get("status") == "DONE" and record.get("resolution") == "UNKNOWN":
                failures.append(f"unknown_done:{work_id}")
        return failures

    def explain(self, node_id: str) -> dict[str, Any]:
        if node_id not in self.nodes:
            raise KeyError(f"unknown_node:{node_id}")
        node = self.nodes[node_id]
        incoming = [e for e in self.edges if e.target == node_id]
        outgoing = [e for e in self.edges if e.source == node_id]
        return {
            "node": {
                "id": node.node_id,
                "kind": node.kind,
                "state": node.state,
                "attributes": node.attrs,
            },
            "incoming": [e.__dict__ for e in incoming],
            "outgoing": [e.__dict__ for e in outgoing],
            "evidence_refs": node.attrs.get("evidence_refs", []),
            "source_refs": node.attrs.get("source_refs", []),
            "authority": self.contract.get("authority", {}),
        }

    def fingerprint(self) -> str:
        payload = {
            "contract": self.contract,
            "registry": self.registry,
            "nodes": [n.__dict__ for n in self.nodes.values()],
            "edges": [e.__dict__ for e in self.edges],
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

    def summary(self) -> dict[str, Any]:
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "unknowns": len(self.unknowns()),
            "conflicts": len(self.conflicts()),
            "logical_space": "10^10+ (bounded, on-demand)",
            "materialization": "forbidden",
            "authority": "descriptive_only",
            "fingerprint": self.fingerprint(),
        }


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", default="current/PLATFORM_VIRTUAL_WORKSPACE_CONTRACT.json")
    parser.add_argument("--registry", default="current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--find-kind")
    parser.add_argument("--find-state")
    parser.add_argument("--trace")
    parser.add_argument("--depth", type=int, default=10)
    parser.add_argument("--explain")
    args = parser.parse_args(argv)

    try:
        graph = PlatformGraph.from_paths(args.contract, args.registry)
        failures = graph.validate()
        if args.validate:
            if failures:
                print("PLATFORM_GRAPH=FAIL")
                print("\n".join(failures))
                return 1
            print("PLATFORM_GRAPH=PASS")
        if args.summary:
            print(json.dumps(graph.summary(), sort_keys=True))
        if args.find_kind or args.find_state:
            print(json.dumps([
                n.__dict__ for n in graph.find(kind=args.find_kind, state=args.find_state)
            ], sort_keys=True))
        if args.trace:
            print(json.dumps(graph.trace(args.trace, depth=args.depth)))
        if args.explain:
            print(json.dumps(graph.explain(args.explain), sort_keys=True))
        if not any((args.validate, args.summary, args.find_kind, args.find_state, args.trace, args.explain)):
            print(json.dumps(graph.summary(), sort_keys=True))
        return 0 if not failures else 1
    except Exception as exc:
        print("PLATFORM_GRAPH=FAIL")
        print(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
