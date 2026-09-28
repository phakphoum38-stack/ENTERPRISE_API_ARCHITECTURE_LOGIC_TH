#!/usr/bin/env python3
"""Read-only architecture completeness inspector.

The inspector never mutates source, branches, history, workflows, or authority.
It validates the machine-readable completeness contract against a repository
checkout and emits deterministic JSON suitable for local use or CI.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_contract(root: Path) -> dict[str, Any]:
    path = root / "current" / "ARCHITECTURE_COMPLETENESS_CONTRACT.json"
    return json.loads(path.read_text(encoding="utf-8"))


def check_file(root: Path, relative: str) -> dict[str, Any]:
    path = root / relative
    return {"path": relative, "exists": path.is_file()}


def inspect(root: Path) -> dict[str, Any]:
    contract = load_contract(root)
    checks: list[dict[str, Any]] = []

    for relative in contract["required_control_documents"]:
        checks.append({"kind": "control_document", **check_file(root, relative)})

    for relative in contract["required_shared_contracts"].values():
        checks.append({"kind": "shared_contract", **check_file(root, relative)})

    for root_name, required in contract["root_requirements"].items():
        for relative in required:
            checks.append(
                {"kind": "flutter_root", **check_file(root, f"{root_name}/{relative}")}
            )

        pubspec = root / root_name / "pubspec.yaml"
        if pubspec.is_file():
            text = pubspec.read_text(encoding="utf-8")
            checks.append(
                {
                    "kind": "shared_contract_dependency",
                    "path": f"{root_name}/pubspec.yaml",
                    "exists": "research_os_contracts:" in text
                    and "../../packages/research_os_contracts" in text,
                }
            )

    dimensions = contract["required_dimensions"]
    controls = contract["dimension_controls"]
    missing_controls = [name for name in dimensions if name not in controls]
    checks.append(
        {
            "kind": "dimension_registry",
            "path": "current/ARCHITECTURE_COMPLETENESS_CONTRACT.json",
            "exists": not missing_controls,
            "missing": missing_controls,
        }
    )

    invariants = contract["global_invariants"]
    checks.append(
        {
            "kind": "invariant_registry",
            "path": "current/ARCHITECTURE_COMPLETENESS_CONTRACT.json",
            "exists": len(invariants) == len(set(invariants)),
            "duplicate_invariants": sorted(
                {x for x in invariants if invariants.count(x) > 1}
            ),
        }
    )

    failures = [c for c in checks if not c["exists"]]
    return {
        "contract_id": contract["contract_id"],
        "schema_version": contract["schema_version"],
        "mode": contract["verification_policy"]["mode"],
        "status": "PASS" if not failures else "FAIL",
        "checked": len(checks),
        "failures": failures,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    result = inspect(args.root.resolve())
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    print(payload, end="")
    if args.json_out:
        args.json_out.write_text(payload, encoding="utf-8")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
