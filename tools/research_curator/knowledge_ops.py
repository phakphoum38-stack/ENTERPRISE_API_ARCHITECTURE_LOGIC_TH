#!/usr/bin/env python3
"""Research Curator v0.3 knowledge operations.

Provides item-level knowledge diff reports and relationship graph exports for
Research Artifact Markdown files. Uses only the Python standard library.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SECTION_NAMES = (
    "Discoveries",
    "Hypotheses",
    "Open Questions",
    "Decisions",
    "Next Actions",
    "Evidence",
)


@dataclass(frozen=True)
class Artifact:
    artifact_id: str
    title: str
    status: str
    path: Path
    sections: dict[str, list[str]]
    relationships: list[tuple[str, str]]


def parse_front_matter(content: str) -> dict[str, str]:
    if not content.startswith("---\n"):
        return {}
    end = content.find("\n---", 4)
    if end < 0:
        return {}
    metadata: dict[str, str] = {}
    for line in content[4:end].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata


def parse_list_section(content: str, heading: str) -> list[str]:
    match = re.search(
        rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)",
        content,
        flags=re.MULTILINE | re.DOTALL,
    )
    if not match:
        return []
    return [
        line[2:].strip()
        for line in match.group(1).splitlines()
        if line.startswith("- ") and "ยังไม่มีรายการ" not in line
    ]


def parse_relationships(content: str) -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    for line in parse_list_section(content, "Relationships"):
        match = re.search(r"`([^`]+)`\s*→\s*`([^`]+)`", line)
        if match:
            results.append((match.group(1), match.group(2)))
    if results:
        return results

    metadata = parse_front_matter(content)
    raw = metadata.get("relationships", "")
    for relation, target in re.findall(r'"([^":]+):([^"\]]+)"', raw):
        results.append((relation, target))
    return results


def load_artifact(path: Path) -> Artifact:
    content = path.read_text(encoding="utf-8")
    metadata = parse_front_matter(content)
    artifact_id = metadata.get("artifact_id", path.stem)
    title = metadata.get("title", artifact_id)
    status = metadata.get("status", "unknown")
    return Artifact(
        artifact_id=artifact_id,
        title=title,
        status=status,
        path=path,
        sections={name: parse_list_section(content, name) for name in SECTION_NAMES},
        relationships=parse_relationships(content),
    )


def normalize_item(value: str) -> str:
    return re.sub(r"\W+", "", value, flags=re.UNICODE).lower()


def diff_items(old: Iterable[str], new: Iterable[str]) -> tuple[list[str], list[str], list[str]]:
    old_map = {normalize_item(item): item for item in old}
    new_map = {normalize_item(item): item for item in new}
    added = [new_map[key] for key in sorted(new_map.keys() - old_map.keys())]
    removed = [old_map[key] for key in sorted(old_map.keys() - new_map.keys())]
    unchanged = [new_map[key] for key in sorted(new_map.keys() & old_map.keys())]
    return added, removed, unchanged


def render_diff(old: Artifact, new: Artifact) -> str:
    lines = [
        f"# Knowledge Diff: {old.artifact_id} → {new.artifact_id}",
        "",
        f"- Old: `{old.path}` ({old.status})",
        f"- New: `{new.path}` ({new.status})",
        "",
    ]
    total_added = total_removed = total_unchanged = 0
    for section in SECTION_NAMES:
        added, removed, unchanged = diff_items(old.sections[section], new.sections[section])
        total_added += len(added)
        total_removed += len(removed)
        total_unchanged += len(unchanged)
        lines.extend([
            f"## {section}",
            "",
            f"- Added: {len(added)}",
            f"- Removed: {len(removed)}",
            f"- Unchanged: {len(unchanged)}",
            "",
        ])
        if added:
            lines.append("### Added")
            lines.extend(f"- {item}" for item in added)
            lines.append("")
        if removed:
            lines.append("### Removed")
            lines.extend(f"- {item}" for item in removed)
            lines.append("")
    lines.extend([
        "## Summary",
        "",
        f"- Total added: {total_added}",
        f"- Total removed: {total_removed}",
        f"- Total unchanged: {total_unchanged}",
        "",
    ])
    return "\n".join(lines)


def load_all(directory: Path) -> list[Artifact]:
    return [load_artifact(path) for path in sorted(directory.glob("RES-*.md"))]


def graph_payload(artifacts: list[Artifact]) -> dict[str, object]:
    nodes = [
        {"id": item.artifact_id, "title": item.title, "status": item.status, "path": str(item.path)}
        for item in artifacts
    ]
    known = {item.artifact_id for item in artifacts}
    edges: list[dict[str, str]] = []
    external: set[str] = set()
    for item in artifacts:
        for relation, target in item.relationships:
            edges.append({"source": item.artifact_id, "relation": relation, "target": target})
            if target not in known:
                external.add(target)
    return {"nodes": nodes, "edges": edges, "external_targets": sorted(external)}


def render_mermaid(payload: dict[str, object]) -> str:
    lines = ["flowchart TD"]
    nodes = payload["nodes"]
    edges = payload["edges"]
    assert isinstance(nodes, list) and isinstance(edges, list)
    for node in nodes:
        assert isinstance(node, dict)
        node_id = str(node["id"])
        label = str(node["title"]).replace('"', "'")
        lines.append(f'  {safe_id(node_id)}["{node_id}: {label}"]')
    for edge in edges:
        assert isinstance(edge, dict)
        source = safe_id(str(edge["source"]))
        target = safe_id(str(edge["target"]))
        relation = str(edge["relation"]).replace('"', "'")
        lines.append(f'  {source} -->|"{relation}"| {target}')
    return "\n".join(lines) + "\n"


def safe_id(value: str) -> str:
    return "N_" + re.sub(r"[^A-Za-z0-9_]", "_", value)


def write_graph(directory: Path, output_prefix: Path) -> tuple[Path, Path]:
    payload = graph_payload(load_all(directory))
    json_path = output_prefix.with_suffix(".json")
    mermaid_path = output_prefix.with_suffix(".mmd")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mermaid_path.write_text(render_mermaid(payload), encoding="utf-8")
    return json_path, mermaid_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Knowledge diff and graph operations")
    sub = parser.add_subparsers(dest="command", required=True)

    diff = sub.add_parser("diff", help="เปรียบเทียบ Artifact แบบรายการต่อรายการ")
    diff.add_argument("--old", required=True)
    diff.add_argument("--new", required=True)
    diff.add_argument("--output")

    graph = sub.add_parser("graph", help="ส่งออก relationship graph เป็น JSON และ Mermaid")
    graph.add_argument("--artifacts", default="research/artifacts")
    graph.add_argument("--output", default="research/graph/knowledge-graph")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "diff":
        report = render_diff(load_artifact(Path(args.old)), load_artifact(Path(args.new)))
        if args.output:
            target = Path(args.output)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(report, encoding="utf-8")
            print(target)
        else:
            print(report)
        return 0
    if args.command == "graph":
        json_path, mermaid_path = write_graph(Path(args.artifacts), Path(args.output))
        print(json.dumps({"json": str(json_path), "mermaid": str(mermaid_path)}, ensure_ascii=False))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
