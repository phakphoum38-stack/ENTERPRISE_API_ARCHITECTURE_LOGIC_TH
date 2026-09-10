#!/usr/bin/env python3
"""Fail-closed source-level audit for the AEOS assurance-check registry."""
from __future__ import annotations

import ast
import importlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "current" / "AEOS_ASSURANCE_CHECK_REGISTRY.json"
SEMANTIC_BOUNDARY = "owner_special/research_os_friend/aeos_source_semantic_checks.py"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class SourceCheckError(RuntimeError):
    pass


def load_registry() -> dict:
    try:
        payload = json.loads(REGISTRY.read_text(encoding="utf-8"))
    except Exception as exc:
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
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def _semantic_result(check_id: str) -> bool:
    try:
        module = importlib.import_module("owner_special.research_os_friend.aeos_source_semantic_checks")
        return bool(module.evaluate(check_id))
    except Exception as exc:
        raise SourceCheckError(f"semantic_evaluation_error:{check_id}:{exc}") from exc


def audit(registry: dict) -> tuple[int, list[str]]:
    errors: list[str] = []
    checks = registry["checks"]
    seen: set[str] = set()
    executable = 0

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
        symbols = source_symbols(path)
        if path.suffix != ".py":
            errors.append(f"source_boundary_not_executable:{check_id}:{boundary}")
            continue
        if not symbols:
            errors.append(f"source_boundary_has_no_callable_logic:{check_id}:{boundary}")
            continue

        required = item.get("required_symbols", [])
        if not isinstance(required, list):
            errors.append(f"required_symbols_not_list:{check_id}")
            continue
        for symbol in required:
            if symbol not in symbols:
                errors.append(f"required_symbol_missing:{check_id}:{symbol}")

        executable += 1

        # The semantic boundary is an executable source auditor over the actual
        # implementation module. A false result is a real SOURCE_GAP and must
        # remain non-certifying; this prevents boolean observation wrappers from
        # manufacturing PASS.
        if boundary == SEMANTIC_BOUNDARY:
            try:
                if not _semantic_result(check_id):
                    errors.append(f"source_semantic_gap:{check_id}:{boundary}")
            except SourceCheckError as exc:
                errors.append(str(exc))

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
        "external_evidence_checks": sum(1 for item in registry["checks"] if item.get("verification_mode", "source") == "external_evidence"),
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
