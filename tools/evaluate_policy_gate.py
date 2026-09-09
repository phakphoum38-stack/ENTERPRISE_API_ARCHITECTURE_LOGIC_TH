#!/usr/bin/env python3
"""Evaluate a compiled P0-06 gate plan with fail-closed semantics."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VALID = {"VERIFIED", "REJECTED", "UNKNOWN", "MISSING", "STALE"}
BLOCKING = {"REJECTED", "UNKNOWN", "MISSING", "STALE"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _state(evidence: dict[str, Any], key: str) -> str:
    raw = evidence.get(key)
    if raw is None:
        return "MISSING"
    if isinstance(raw, str):
        state = raw
    elif isinstance(raw, dict):
        state = raw.get("state", "MISSING")
    else:
        return "UNKNOWN"
    return state if state in VALID else "UNKNOWN"


def evaluate(plan: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    results = []
    approval_pending = False
    for rule in plan.get("rules", []):
        reasons = []
        states = {}
        for key in rule["required_evidence"]:
            state = _state(evidence, key)
            states[key] = state
            if state in BLOCKING:
                reasons.append(f"{key}:{state}")
        if reasons:
            decision = "BLOCK"
        else:
            decision = "PASS"
            if rule.get("approval_mode") == "REQUIRED":
                approval_state = _state(evidence, "human_approval")
                if approval_state == "UNKNOWN" or approval_state in BLOCKING:
                    decision = "BLOCK"
                    reasons.append(f"human_approval:{approval_state}")
                elif approval_state == "PENDING":
                    decision = "REQUIRE_APPROVAL"
                    approval_pending = True
        results.append({
            "rule_id": rule["rule_id"],
            "decision": decision,
            "evidence_states": states,
            "reason_codes": reasons,
        })

    gate_results = []
    for gate in plan.get("gates", []):
        members = [r for r in results if r["rule_id"] in gate["rule_ids"]]
        decisions = [r["decision"] for r in members]
        if gate["mode"] in {"ALL", "SEQUENCE"}:
            if "BLOCK" in decisions:
                gd = "BLOCK"
            elif "REQUIRE_APPROVAL" in decisions:
                gd = "REQUIRE_APPROVAL"
            else:
                gd = "PASS"
        elif gate["mode"] == "ANY":
            if "PASS" in decisions:
                gd = "PASS"
            elif "REQUIRE_APPROVAL" in decisions:
                gd = "REQUIRE_APPROVAL"
            else:
                gd = "BLOCK"
        else:
            gd = "BLOCK"
        gate_results.append({"gate_id": gate["gate_id"], "decision": gd, "rule_decisions": decisions})

    if any(g["decision"] == "BLOCK" for g in gate_results):
        decision = "BLOCK"
    elif any(g["decision"] == "REQUIRE_APPROVAL" for g in gate_results) or approval_pending:
        decision = "REQUIRE_APPROVAL"
    elif gate_results and all(g["decision"] == "PASS" for g in gate_results):
        decision = "PASS"
    else:
        decision = "BLOCK"

    receipt = {
        "receipt_type": "P0-06-EVALUATION",
        "compiler_version": plan.get("compiler_version"),
        "policy_id": plan.get("policy_id"),
        "policy_version": plan.get("policy_version"),
        "policy_fingerprint": plan.get("policy_fingerprint"),
        "plan_fingerprint": plan.get("plan_fingerprint"),
        "gate_results": gate_results,
        "decision": decision,
        "reason_codes": sorted({reason for r in results for reason in r["reason_codes"]}),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "authority_effect": "NONE",
    }
    material = dict(receipt)
    material.pop("evaluated_at", None)
    receipt["evaluation_fingerprint"] = hashlib.sha256(canonical_json(material)).hexdigest()
    return receipt


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: evaluate_policy_gate.py PLAN.json EVIDENCE.json", file=sys.stderr)
        return 2
    plan = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    evidence = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    receipt = evaluate(plan, evidence)
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if receipt["decision"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
