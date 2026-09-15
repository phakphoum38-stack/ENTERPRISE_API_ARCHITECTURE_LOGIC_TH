#!/usr/bin/env python3
"""Generate target-bound runtime evidence and a provenance ledger.

The generated files are runtime evidence, not source-of-truth fixtures. The
producer records only observations it is authoritative to make; independent
verification is performed later by tools/validate_provenance_evidence.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

DOMAIN = b"provenance-entry-v1\x00"
ROOT = Path(__file__).resolve().parents[1]


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: object) -> str:
    return hashlib.sha256(DOMAIN + canonical(value).encode("utf-8")).hexdigest()


def plain_digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="target-provenance")
    args = parser.parse_args()

    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)

    target = git("rev-parse", "HEAD")
    source = git("rev-parse", "HEAD^")
    run_id = os.environ.get("GITHUB_RUN_ID", "unknown")
    workflow = os.environ.get("GITHUB_WORKFLOW", "Provenance Evidence Gate")
    recorded_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    changed = git("diff-tree", "--no-commit-id", "--name-only", "-r", target).splitlines()
    tree = git("show", "-s", "--format=%T", target)

    evidence = {
        "schema_version": "1.0",
        "evidence_id": f"EV-TARGET-{target[:12]}",
        "workflow": workflow,
        "run_id": run_id,
        "target_commit": target,
        "source_commit": source,
        "commit_tree": tree,
        "changed_paths": changed,
        "recorded_at": recorded_at,
    }
    evidence_path = out / "TARGET_BOUND_EVIDENCE.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    evidence_root = plain_digest(evidence)

    attestation_id = f"AT-TARGET-{target[:12]}"
    attestation = {
        "entry_id": attestation_id,
        "sequence": 1,
        "recorded_at": recorded_at,
        "actor_id": "github-actions:provenance-evidence-gate",
        "action": "attest_target_generation",
        "subject_type": "git-commit",
        "subject_id": target,
        "input_hashes": {
            "source_commit": {"algorithm": "git-sha1", "digest": source, "subject": "git-commit"}
        },
        "output_hashes": {
            "target_commit": {"algorithm": "git-sha1", "digest": target, "subject": "git-commit"},
            "evidence": {"algorithm": "sha256", "digest": evidence_root, "subject": "artifact:target-provenance/TARGET_BOUND_EVIDENCE.json"},
        },
        "evidence_type": "attestation",
        "evidence": {
            "attestation_id": attestation_id,
            "subject_id": target,
            "attester_id": "github-actions:provenance-evidence-gate",
            "statement": "The exact target generation and its runtime evidence were observed in this workflow run.",
            "evidence_ids": [],
            "issued_at": recorded_at,
        },
        "previous_entry_hash": None,
    }
    attestation["entry_hash"] = digest(attestation)

    ledger = {
        "contract_version": "1.1.0",
        "entries": [attestation],
    }
    ledger_path = out / "TARGET_BOUND_PROVENANCE.json"
    ledger_path.write_text(json.dumps(ledger, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    provenance_root = plain_digest(ledger)

    roots = {
        "schema_version": "1.0",
        "target_commit": target,
        "source_commit": source,
        "evidence_root": evidence_root,
        "provenance_root": provenance_root,
        "evidence_file": str(evidence_path.relative_to(ROOT)).replace("\\", "/"),
        "provenance_file": str(ledger_path.relative_to(ROOT)).replace("\\", "/"),
    }
    (out / "TARGET_BOUND_ROOTS.json").write_text(json.dumps(roots, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(roots, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
