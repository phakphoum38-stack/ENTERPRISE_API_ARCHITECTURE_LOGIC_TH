#!/usr/bin/env python3
"""Reusable Platform operationalization boundary.

This layer is deliberately read-only. It turns the already-canonical Platform
composition and M.2 capabilities into an operational contract for continuity,
impact guarding, lifecycle classification and evidence reconciliation.

It does not execute work, mutate runtime state, authorize, merge or release.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from tools.platform_service import PlatformService

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "current/PLATFORM_OPERATIONALIZATION_CONTRACT.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REQUIRED_SNAPSHOT_FIELDS = {
    "repository", "source_sha", "protected_baseline_sha", "active_work",
    "deferred_work", "decisions", "verified_truths", "evidence_refs",
    "open_risks", "unknowns", "authority_boundaries", "next_action",
}
IMPACT_CATEGORIES = (
    "contracts", "workflows", "tests", "final_gate", "invariants", "product_surfaces",
)


def canonical_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


class PlatformOperationalization:
    """Source-pinned, read-only operational boundary for the Platform."""

    def __init__(self, service: PlatformService | None = None) -> None:
        self.service = service or PlatformService()
        self.source_sha = canonical_sha()

    def snapshot(
        self,
        *,
        active_work: list[str] | None = None,
        deferred_work: list[str] | None = None,
        decisions: list[str] | None = None,
        verified_truths: list[str] | None = None,
        evidence_refs: list[str] | None = None,
        open_risks: list[str] | None = None,
        unknowns: list[str] | None = None,
        next_action: str = "recon_then_impact_guard",
    ) -> dict[str, Any]:
        return {
            "repository": "phakphoum38-stack/ENTERPRISE_API_ARCHITECTURE_LOGIC_TH",
            "source_sha": self.source_sha,
            "protected_baseline_sha": self.source_sha,
            "active_work": active_work or [],
            "deferred_work": deferred_work or [],
            "decisions": decisions or [],
            "verified_truths": verified_truths or [],
            "evidence_refs": evidence_refs or [],
            "open_risks": open_risks or [],
            "unknowns": unknowns or [],
            "authority_boundaries": {
                "platform_may_execute": False,
                "platform_may_authorize": False,
                "platform_may_approve": False,
                "platform_may_merge": False,
                "platform_may_release": False,
                "release_authority": "FINAL_GATE",
            },
            "next_action": next_action,
        }

    def validate_snapshot(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        current = canonical_sha()
        failures: list[str] = []
        missing = sorted(REQUIRED_SNAPSHOT_FIELDS - set(snapshot))
        if missing:
            failures.append("missing_required_fields:" + ",".join(missing))
        if not SHA_RE.fullmatch(str(snapshot.get("source_sha", ""))):
            failures.append("invalid_source_sha")
        elif snapshot["source_sha"] != current:
            failures.append("source_sha_mismatch")
        if not SHA_RE.fullmatch(str(snapshot.get("protected_baseline_sha", ""))):
            failures.append("invalid_protected_baseline_sha")
        if snapshot.get("unknowns"):
            failures.append("unknowns_present")
        boundaries = snapshot.get("authority_boundaries", {})
        if boundaries.get("release_authority") != "FINAL_GATE":
            failures.append("invalid_release_authority")
        if any(boundaries.get(k) is not False for k in (
            "platform_may_execute", "platform_may_authorize",
            "platform_may_approve", "platform_may_merge", "platform_may_release",
        )):
            failures.append("authority_boundary_violation")
        evidence_failures = self._evidence_refs(snapshot.get("evidence_refs", []))
        failures.extend(evidence_failures)
        return {
            "status": "HOLD" if failures else "PASS",
            "source_sha": current,
            "snapshot_sha": snapshot.get("source_sha"),
            "failures": failures,
            "deferred_work": snapshot.get("deferred_work", []),
        }

    def impact_guard(self, query: str) -> dict[str, Any]:
        result = self.service.impact(query)
        impact = result.get("impact", {})
        missing = [k for k in IMPACT_CATEGORIES if not impact.get(k)]
        return {
            "status": "HOLD" if result.get("source_sha") != canonical_sha() or missing or result.get("unknown") else "PASS",
            "source_sha": canonical_sha(),
            "query": query,
            "impact": impact,
            "missing_categories": missing,
            "unknown": bool(result.get("unknown")),
            "next_action": "inspect_missing_impact_and_hold" if (missing or result.get("unknown")) else "safe_to_proceed_to_planning",
        }

    def lifecycle_classify(self, state: str) -> dict[str, str]:
        normalized = state.strip().upper()
        actions = {
            "DISCOVER": "RECON",
            "PLAN": "IMPACT_GUARD",
            "EXECUTE": "EXTERNAL_EXECUTION_PLANE",
            "VERIFY": "EVIDENCE_RECONCILE",
            "DEFERRED": "PRESERVE_AND_RETURN",
            "UNKNOWN": "HOLD",
            "CONFLICT": "REJECT_AND_RELEASE",
            "RELEASE": "FINAL_GATE_ONLY",
        }
        action = actions.get(normalized, "HOLD")
        return {
            "state": normalized,
            "action": action,
            "status": "HOLD" if action == "HOLD" else "CLASSIFIED",
        }

    def evidence_reconcile(self, refs: list[str]) -> dict[str, Any]:
        failures = self._evidence_refs(refs)
        return {
            "status": "HOLD" if failures else "PASS",
            "source_sha": canonical_sha(),
            "references": refs,
            "failures": failures,
        }

    def resume(self, snapshot: dict[str, Any]) -> dict[str, Any]:
        validation = self.validate_snapshot(snapshot)
        return {
            "status": "HOLD" if validation["status"] != "PASS" else "READY_FOR_RECON",
            "source_sha": canonical_sha(),
            "snapshot_validation": validation,
            "deferred_work": snapshot.get("deferred_work", []),
            "next_action": (
                "repair_snapshot_then_reverify"
                if validation["status"] != "PASS"
                else "run_recon_then_impact_guard"
            ),
        }

    @staticmethod
    def _evidence_refs(refs: list[str]) -> list[str]:
        failures: list[str] = []
        for ref in refs:
            path = ROOT / ref
            if not path.is_file():
                failures.append("missing_evidence:" + ref)
        return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", action="store_true")
    parser.add_argument("--validate-snapshot")
    parser.add_argument("--resume")
    parser.add_argument("--impact")
    parser.add_argument("--lifecycle")
    parser.add_argument("--evidence", nargs="*")
    args = parser.parse_args()
    service = PlatformOperationalization()
    if args.snapshot:
        payload = service.snapshot()
    elif args.validate_snapshot:
        payload = service.validate_snapshot(json.loads(Path(args.validate_snapshot).read_text(encoding="utf-8")))
    elif args.resume:
        payload = service.resume(json.loads(Path(args.resume).read_text(encoding="utf-8")))
    elif args.impact:
        payload = service.impact_guard(args.impact)
    elif args.lifecycle:
        payload = service.lifecycle_classify(args.lifecycle)
    elif args.evidence is not None:
        payload = service.evidence_reconcile(args.evidence)
    else:
        parser.error("select an operation")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
