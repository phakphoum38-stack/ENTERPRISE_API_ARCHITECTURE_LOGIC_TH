#!/usr/bin/env python3
"""Extract and classify a Control Center payload without mutating source.

This is a forensic extractor. It never treats UI presence as proof of capability,
authority, evidence, or lineage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

SYMBOL_PATTERNS = [
    re.compile(r"^\s*(?:abstract\s+)?class\s+(\w+)", re.M),
    re.compile(r"^\s*(?:enum|extension|mixin)\s+(\w+)", re.M),
    re.compile(r"^\s*(?:static\s+)?(?:const|final)\s+(?:\w+[<>,.? ]*\s+)?(\w+)\s*=", re.M),
    re.compile(r"^\s*(?:Future<[^>]+>|void|bool|int|String|double|Widget|List<[^>]+>|Map<[^>]+>|[A-Z]\w*)\s+(\w+)\s*\(", re.M),
]


def run(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_text(ref: str, path: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{path}"], cwd=ROOT, text=True
        )
    except subprocess.CalledProcessError:
        return None


def changed_paths(base: str, payload: str) -> list[str]:
    out = run("diff", "--name-only", base, payload)
    return [line.strip() for line in out.splitlines() if line.strip()]


def symbols(text: str) -> list[str]:
    found: list[str] = []
    for pattern in SYMBOL_PATTERNS:
        found.extend(pattern.findall(text))
    return sorted(set(found))


def classify(path: str, text: str) -> dict[str, Any]:
    lower = path.lower() + "\n" + text.lower()
    imports = re.findall(r"^import ['\"]([^'\"]+)['\"];?", text, re.M)
    real_api = any(
        x in lower
        for x in (
            "research_os_api_client",
            "gethealth()",
            "getbraincapacity()",
            "getproviders()",
            "getagents()",
        )
    )
    projection = any(
        x in lower
        for x in (
            "unknown is preserved",
            "descriptive_only",
            "canonical closure projection",
            "runtime observation",
        )
    )
    authority = (
        any(x in lower for x in ("authorize", "approval", "release", "merge"))
        and "external" in lower
    )
    local_editor = "source buffer" in lower or "filecodeworkspace" in lower

    if "root_closure" in path.lower():
        kind = "PROJECTION_ONLY"
    elif local_editor:
        kind = "LOCAL_UI_TOOL"
    elif real_api:
        kind = "REAL_API_OBSERVATION"
    elif projection:
        kind = "UI_PROJECTION"
    else:
        kind = "UI_OR_SUPPORTING_CODE"

    return {
        "kind": kind,
        "real_api_observation": real_api,
        "authority_boundary_text_present": authority,
        "local_editor": local_editor,
        "imports": imports,
        "symbols": symbols(text),
        "sha256": sha256_bytes(text.encode()),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload-ref", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    run("cat-file", "-e", f"{args.payload_ref}^{{commit}}")
    run("cat-file", "-e", f"{args.base_ref}^{{commit}}")

    paths = changed_paths(args.base_ref, args.payload_ref)
    dart_paths = [p for p in paths if p.endswith(".dart")]
    records = []

    for path in dart_paths:
        text = git_text(args.payload_ref, path)
        if text is None:
            continue
        rec = classify(path, text)
        rec.update(
            {
                "path": path,
                "payload_ref": args.payload_ref,
                "base_present": git_text(args.base_ref, path) is not None,
                "payload_present": True,
            }
        )
        records.append(rec)

    result = {
        "version": 1,
        "mode": "forensic-extraction-only",
        "payload_ref": args.payload_ref,
        "base_ref": args.base_ref,
        "payload_commit_tree": run("rev-parse", f"{args.payload_ref}^{{tree}}"),
        "changed_paths": paths,
        "dart_records": records,
        "rules": {
            "ui_presence_is_not_capability": True,
            "projection_is_not_authority": True,
            "unknown_is_preserved": True,
            "no_source_mutation": True,
            "no_history_rewrite": True,
            "no_automatic_integration": True,
        },
    }

    out = ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "payload_ref": args.payload_ref,
                "base_ref": args.base_ref,
                "changed_paths": len(paths),
                "dart_records": len(records),
                "output": str(out),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
