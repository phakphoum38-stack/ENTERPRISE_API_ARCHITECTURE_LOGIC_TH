#!/usr/bin/env python3
"""Turn a failed GitHub Actions log into a deterministic, safety-aware repair plan."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
PROTECTED = {"TARGET_SHA", "OWNER_BUILD_IDENTITY", "SHA256", "INSTALLED_PROVENANCE", "CANONICAL_LINEAGE", "RELEASE_CERTIFICATION"}

PATTERNS = [
    ("TRANSIENT_NETWORK", re.compile(r"(timed out|connection reset|502 bad gateway|503 service unavailable|429)", re.I), "retry_allowed"),
    ("STALE_LASTEXITCODE", re.compile(r"LASTEXITCODE.*(stale|exit code 1|false|failed).*(PowerShell|script)|script.*PASS.*exit code 1", re.I | re.S), "safe_patch_candidate"),
    ("TARGET_SHA_MISMATCH", re.compile(r"SOURCE_SHA_MISMATCH|target.*sha.*checkout.*sha|TARGET_SHA.*mismatch", re.I), "protected_stop"),
    ("PROVENANCE_FAILURE", re.compile(r"RELEASE_PROVENANCE_GATE=FAIL|provenance.*failed|installed.*commit.*mismatch|installed.*sha256.*mismatch", re.I), "protected_stop"),
    ("IDENTITY_FAILURE", re.compile(r"identity.*gate.*fail|BUILD_IDENTITY.*FAIL|branding.*mismatch", re.I), "protected_stop"),
    ("ARTIFACT_FAILURE", re.compile(r"artifact.*not found|download-artifact.*fail|upload-artifact.*fail", re.I), "investigate_artifact_lineage"),
    ("FLUTTER_TEST_FAILURE", re.compile(r"flutter test.*fail|test failed|TestWidgetsFlutterBinding|No tests ran", re.I), "test_first"),
    ("YAML_FAILURE", re.compile(r"yaml.*(parse|syntax)|mapping values are not allowed|did not find expected", re.I), "static_yaml_validation"),
]


def classify(text: str) -> tuple[str, str]:
    for code, pattern, action in PATTERNS:
        if pattern.search(text):
            return code, action
    return "UNKNOWN_FAILURE", "human_review"


def protected_hit(text: str) -> list[str]:
    hits = []
    normalized = re.sub(r"[^A-Z0-9]+", "_", text.upper())
    for item in sorted(PROTECTED):
        if item in normalized:
            hits.append(item)
    return hits


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--log", required=True, help="failure log text file")
    p.add_argument("--workflow", default="unknown")
    p.add_argument("--run-id", default="unknown")
    args = p.parse_args()
    text = Path(args.log).read_text(encoding="utf-8", errors="replace")
    code, action = classify(text)
    protected = protected_hit(text)
    if action == "protected_stop" or protected and code in {"UNKNOWN_FAILURE", "TARGET_SHA_MISMATCH", "PROVENANCE_FAILURE", "IDENTITY_FAILURE"}:
        status = "HUMAN_APPROVAL_REQUIRED"
    elif action == "retry_allowed":
        status = "AUTO_RETRY_CANDIDATE"
    elif action == "safe_patch_candidate":
        status = "SAFE_REPAIR_CANDIDATE"
    else:
        status = "ANALYSIS_REQUIRED"
    plan = {
        "version": 1,
        "workflow": args.workflow,
        "run_id": args.run_id,
        "classification": code,
        "recommended_action": action,
        "status": status,
        "protected_gate_mentions": protected,
        "auto_apply_to_main": False,
        "auto_merge": False,
        "repair_rules": [
            "never weaken protected gates",
            "never replace immutable TARGET_SHA with github.sha",
            "never delete identity/provenance/lineage checks",
            "keep repair branch isolated",
            "validate before creating a PR",
        ],
    }
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "WORKFLOW_FAILURE_ANALYSIS.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
