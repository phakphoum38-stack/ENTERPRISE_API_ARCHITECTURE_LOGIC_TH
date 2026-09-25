#!/usr/bin/env python3
"""Platform-level M.2 discovery facade built on the existing audit index.\n\nContract: current/RESEARCH_OS_M2_PLATFORM_CONTRACT.json.

M.2 remains descriptive/read-only. It does not authorize, merge, release, or
mutate runtime state. The facade adds vertical/horizontal search, bounded
relationship traversal, impact inspection, and resume-state extraction.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from tools.research_os_m2_audit import build_index
from tools.platform_graph import PlatformGraph

ROOT = Path(__file__).resolve().parents[1]
MAX_DEPTH = 32
MAX_RESULTS = 256


class M2Platform:
    """Read-only platform discovery service over the canonical M.2 index."""

    def __init__(self, index: dict[str, Any] | None = None) -> None:
        self.index = index or build_index()
        self.nodes = {n["id"]: n for n in self.index["nodes"]}
        self.edges = list(self.index["edges"])
        self._out: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._in: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for edge in self.edges:
            self._out[edge["from"]].append(edge)
            self._in[edge["to"]].append(edge)

    @property
    def source_sha(self) -> str:
        return self.index["source_sha"]

    def search(self, query: str, *, limit: int = MAX_RESULTS) -> list[dict[str, Any]]:
        q = query.strip().lower()
        if not q:
            raise ValueError("query_must_not_be_empty")
        matches = []
        for node in self.nodes.values():
            haystack = " ".join([
                str(node.get("id", "")),
                str(node.get("path", "")),
                str(node.get("kind", "")),
                json.dumps(node.get("attributes", {}), sort_keys=True),
            ]).lower()
            if q in haystack:
                matches.append(node)
            if len(matches) >= limit:
                break
        return matches

    def vertical(self, query: str, *, depth: int = 10) -> dict[str, Any]:
        if depth < 0 or depth > MAX_DEPTH:
            raise ValueError(f"depth_must_be_between_0_and_{MAX_DEPTH}")
        roots = self.search(query)
        discovered: list[str] = []
        seen: set[str] = set()
        queue: deque[tuple[str, int]] = deque((n["id"], 0) for n in roots)
        while queue and len(discovered) < MAX_RESULTS:
            node_id, level = queue.popleft()
            if node_id in seen:
                continue
            seen.add(node_id)
            discovered.append(node_id)
            if level >= depth:
                continue
            for edge in self._out.get(node_id, []):
                queue.append((edge["to"], level + 1))
        return {
            "query": query,
            "source_sha": self.source_sha,
            "roots": [n["id"] for n in roots],
            "nodes": [self.nodes[n] for n in discovered if n in self.nodes],
            "edges": [
                e for e in self.edges
                if e["from"] in seen and e["to"] in seen
            ],
        }

    def horizontal(self, query: str, *, limit: int = MAX_RESULTS) -> dict[str, Any]:
        roots = self.search(query)
        root_ids = {n["id"] for n in roots}
        related: list[dict[str, Any]] = []
        seen_edges: set[tuple[str, str, str]] = set()
        for edge in self.edges:
            if edge["from"] in root_ids or edge["to"] in root_ids:
                key = (edge["from"], edge["relation"], edge["to"])
                if key not in seen_edges:
                    seen_edges.add(key)
                    related.append(edge)
            if len(related) >= limit:
                break
        related_ids = {e["from"] for e in related} | {e["to"] for e in related}
        related_ids -= root_ids
        return {
            "query": query,
            "source_sha": self.source_sha,
            "roots": roots,
            "relations": related,
            "related_nodes": [
                self.nodes[n] for n in related_ids if n in self.nodes
            ][:limit],
        }

    def impact(self, query: str) -> dict[str, Any]:
        result = self.vertical(query, depth=MAX_DEPTH)
        node_ids = {n["id"] for n in result["nodes"]}
        categories = {
            "contracts": [],
            "workflows": [],
            "tests": [],
            "final_gate": [],
            "invariants": [],
            "product_surfaces": [],
        }
        for node_id in node_ids:
            node = self.nodes[node_id]
            kind = str(node.get("kind", "")).upper()
            path = str(node.get("path", ""))
            if kind == "CONTRACT" or "/current/" in path:
                categories["contracts"].append(node_id)
            if kind == "WORKFLOW" or ".github/workflows/" in path:
                categories["workflows"].append(node_id)
            if kind == "TEST" or "/test" in path or path.startswith("tools/test_"):
                categories["tests"].append(node_id)
            if "FINAL_GATE" in node_id or "final_gate" in json.dumps(node).lower():
                categories["final_gate"].append(node_id)
            if kind == "INVARIANT":
                categories["invariants"].append(node_id)
            if "apps/research_os_flutter" in path or "owner_special/flutter_app" in path:
                categories["product_surfaces"].append(node_id)
        return {
            "query": query,
            "source_sha": self.source_sha,
            "impact": categories,
            "unknown": any(v == [] for v in categories.values()),
        }

    def platform_graph_summary(self) -> dict[str, Any]:
        graph = PlatformGraph.from_paths(
            ROOT / "current/PLATFORM_VIRTUAL_WORKSPACE_CONTRACT.json",
            ROOT / "current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json",
        )
        failures = graph.validate()
        return {
            "summary": graph.summary(),
            "validation_failures": failures,
            "authority": "descriptive_only",
        }

    def resume(self) -> dict[str, Any]:
        files = self.index["files"]
        active = [
            r["path"] for r in files
            if r.get("kind") in {"implementation", "script"}
            and r.get("final_gate_refs")
        ]
        deferred = [
            r["path"] for r in files
            if "DEFERRED" in json.dumps(r).upper()
        ]
        return {
            "source_sha": self.source_sha,
            "chat_is_not_source_of_truth": True,
            "active_work_candidates": active[:MAX_RESULTS],
            "deferred_candidates": deferred[:MAX_RESULTS],
            "integrity": self.index["integrity"],
            "platform_graph": self.platform_graph_summary(),
            "next_step": "Reconcile snapshot and inspect impact before mutation.",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query")
    parser.add_argument("--vertical", action="store_true")
    parser.add_argument("--horizontal", action="store_true")
    parser.add_argument("--impact", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--depth", type=int, default=10)
    args = parser.parse_args()

    service = M2Platform()
    if args.resume:
        payload = service.resume()
    elif not args.query:
        parser.error("--query is required unless --resume is used")
    elif args.horizontal:
        payload = service.horizontal(args.query)
    elif args.impact:
        payload = service.impact(args.query)
    else:
        payload = service.vertical(args.query, depth=args.depth) if args.vertical else {
            "source_sha": service.source_sha,
            "results": service.search(args.query),
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
