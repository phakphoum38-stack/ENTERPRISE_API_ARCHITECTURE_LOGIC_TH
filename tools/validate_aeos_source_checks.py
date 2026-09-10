#!/usr/bin/env python3
"""Fail-closed source-level audit for the AEOS assurance-check registry.

A registry entry is not a test merely because it has an id or a boundary path.
For a check to qualify as source-level executable verification, the boundary
must exist, parse as Python when applicable, and expose executable logic that
can be traced to a callable symbol or a concrete validator entry point.

Entries explicitly marked external are evidence requirements, not executable
source tests. They remain non-certifying until independently supplied proof is
bound and verified by the assurance fabric.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "current" / "AEOS_ASSURANCE_CHECK_REGISTRY.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class SourceCheckError(RuntimeError):
    pass


def load_registry() -> dict:
    try:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - exercised by CI on corruption
        raise SourceCheckError(f"registry_unreadable:{exc}") from exc
    if payload.get("policy") != "fail_closed":
        raise SourceCheckError("registry_policy_not_fail_closed")
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        raise SourceCheckError("registry_checks_missing")
    return payload


def source_symbols(path: Path) -> set[str]:
    if path.suffix != ".py":
        return set()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError as exc:
        raise SourceCheckError(f"syntax_error:{path}:{exc}") from exc
    symbols: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
    return symbols


def audit(registry: dict) -> tuple[int, list[str]]:
    errors: list[str] = []
    checks = registry["checks"]
    seen: set[str] = set()
    executable = 0
    external = 0

    for item in checks:
        check_id = item.get("id")
        if not isinstance(check_id, str) or not check_id:
            errors.append("invalid_check_id")
            continue
        if check_id in seen:
            errors.append(f"duplicate_check:{check_id}")
        seen.add(check_id)

        mode = item.get("verification_mode", "source")
        boundary = item.get("boundary")

        if mode == "external_evidence":
            external += 1
            if boundary is not None:
                errors.append(f"external_check_has_boundary:{check_id}")
            continue

        if mode != "source":
            errors.append(f"unknown_verification_mode:{check_id}:{mode}")
            continue
        if not isinstance(boundary, str) or not boundary:
            errors.append(f"source_check_missing_boundary:{check_id}")
            continue

        path = ROOT / boundary
        if not path.is_file():
            errors.append(f"source_boundary_missing:{check_id}:{boundary}")
            continue

        try:
            symbols = source_symbols(path)
        except SourceCheckError as exc:
            errors.append(str(exc))
            continue

        # A non-Python boundary must be explicitly declared as external or
        # composite; file existence alone is never sufficient for TEST.
        if path.suffix != ".py":
            errors.append(f"source_boundary_not_executable:{check_id}:{boundary}")
            continue
        if not symbols:
            errors.append(f"source_boundary_has_no_callable_logic:{check_id}:{boundary}")
            continue

        # Optional symbol contract: when present, the named symbol must really
        # exist in the boundary source. This prevents check-name-only assurance.
        required = item.get("required_symbols", [])
        if not isinstance(required, list):
            errors.append(f"required_symbols_not_list:{check_id}")
            continue
        for symbol in required:
            if symbol not in symbols:
                errors.append(f"required_symbol_missing:{check_id}:{symbol}")

        executable += 1

    if len(seen) != len(checks):
        errors.append("registry_identity_not_unique")
    return executable, errors


def main() -> int:
    registry = load_registry()
    baseline = registry.get("baseline_sha")
    if not isinstance(baseline, str) or not SHA_RE.fullmatch(baseline):
        raise SourceCheckError("invalid_registry_baseline_sha")

    executable, errors = audit(registry)
    print(json.dumps({
        "checks": len(registry["checks"]),
        "executable_source_checks": executable,
        "external_evidence_checks": sum(
            1 for item in registry["checks"]
            if item.get("verification_mode", "source") == "external_evidence"
        ),
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SourceCheckError as exc:
        print(json.dumps({"status": "FAIL", "errors": [str(exc)]}, sort_keys=True))
        raise SystemExit(1)
