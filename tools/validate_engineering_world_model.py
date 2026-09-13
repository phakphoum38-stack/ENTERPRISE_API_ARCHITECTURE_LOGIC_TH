#!/usr/bin/env python3
"""Validate the canonical Engineering World Model graph."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ISO8601 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def validate(schema_path: Path, graph_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    types = set(schema["entities"])
    rel_types = set(schema["relationships"])
    states = set(schema["lifecycle_states"])
    entities = graph.get("entities", [])
    relationships = graph.get("relationships", [])
    ids = [e.get("id") for e in entities]
    if len(ids) != len(set(ids)):
        errors.append("duplicate entity id")
    known = set(ids)
    for e in entities:
        for field in schema["required_entity_fields"]:
            if field not in e:
                errors.append(f"entity {e.get('id')}: missing {field}")
        if e.get("type") not in types:
            errors.append(f"entity {e.get('id')}: undeclared type")
        if e.get("state") not in states:
            errors.append(f"entity {e.get('id')}: undeclared state")
        for field in ("created_at", "valid_from"):
            if field in e and not ISO8601.match(e[field]):
                errors.append(f"entity {e.get('id')}: invalid {field}")
    rel_ids = [r.get("id") for r in relationships]
    if len(rel_ids) != len(set(rel_ids)):
        errors.append("duplicate relationship id")
    for r in relationships:
        for field in schema["required_relationship_fields"]:
            if field not in r:
                errors.append(f"relationship {r.get('id')}: missing {field}")
        if r.get("type") not in rel_types:
            errors.append(f"relationship {r.get('id')}: undeclared type")
        if r.get("from") not in known or r.get("to") not in known:
            errors.append(f"relationship {r.get('id')}: endpoint missing")
        if "valid_from" in r and not ISO8601.match(r["valid_from"]):
            errors.append(f"relationship {r.get('id')}: invalid valid_from")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, default=Path("current/ENGINEERING_WORLD_MODEL_SCHEMA.json"))
    parser.add_argument("--graph", type=Path, default=Path("current/ENGINEERING_WORLD_MODEL_FIXTURE.json"))
    args = parser.parse_args()
    try:
        errors = validate(args.schema, args.graph)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        print(json.dumps({"status": "FAIL", "errors": [str(exc)]}, sort_keys=True))
        return 1
    report = {"status": "FAIL" if errors else "PASS", "errors": errors, "entity_count": 0 if errors and not args.graph.exists() else len(json.loads(args.graph.read_text(encoding="utf-8")).get("entities", []))}
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
