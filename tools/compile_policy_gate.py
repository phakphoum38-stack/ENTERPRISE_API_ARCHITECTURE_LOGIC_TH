#!/usr/bin/env python3
"""Compile a P0-06 policy into a deterministic gate plan."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ALLOWED_MODES = {"ALL", "ANY", "SEQUENCE"}
ALLOWED_APPROVAL = {"NONE", "REQUIRED"}
HIGH_RISK_CLASSES = {
    "high", "authority_change", "constitutional_amendment", "production_mutation",
    "release_promotion", "installed_artifact_change", "security_policy_change",
    "identity_or_capability_revocation",
}
REQUIRED_POLICY = {"policy_id", "policy_version", "policy_fingerprint", "lineage", "rules", "gates"}
REQUIRED_RULE = {"rule_id", "risk_class", "required_evidence", "approval_mode", "on_unknown", "on_failure"}
REQUIRED_GATE = {"gate_id", "rule_ids", "mode"}


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def policy_fingerprint(policy: dict[str, Any]) -> str:
    material = {k: v for k, v in policy.items() if k != "policy_fingerprint"}
    return hashlib.sha256(canonical_json(material)).hexdigest()


def compile_policy(policy: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_POLICY - policy.keys())
    if missing:
        raise ValueError(f"missing_policy_fields:{','.join(missing)}")
    if not isinstance(policy["rules"], list) or not isinstance(policy["gates"], list):
        raise ValueError("rules_and_gates_must_be_lists")
    actual = policy_fingerprint(policy)
    if policy["policy_fingerprint"] != actual:
        raise ValueError("invalid_policy_fingerprint")

    rules: dict[str, dict[str, Any]] = {}
    for rule in policy["rules"]:
        if not isinstance(rule, dict):
            raise ValueError("rule_must_be_object")
        missing_rule = sorted(REQUIRED_RULE - rule.keys())
        if missing_rule:
            raise ValueError(f"missing_rule_fields:{','.join(missing_rule)}")
        rule_id = rule["rule_id"]
        if not isinstance(rule_id, str) or not rule_id:
            raise ValueError("invalid_rule_id")
        if rule_id in rules:
            raise ValueError(f"duplicate_rule:{rule_id}")
        if rule["approval_mode"] not in ALLOWED_APPROVAL:
            raise ValueError(f"invalid_approval_mode:{rule_id}")
        if rule["risk_class"] in HIGH_RISK_CLASSES and rule["approval_mode"] != "REQUIRED":
            raise ValueError(f"high_risk_requires_approval:{rule_id}")
        if rule["on_unknown"] != "BLOCK" or rule["on_failure"] != "BLOCK":
            raise ValueError(f"rule_not_fail_closed:{rule_id}")
        if not isinstance(rule["required_evidence"], list) or not rule["required_evidence"]:
            raise ValueError(f"invalid_required_evidence:{rule_id}")
        rules[rule_id] = rule

    gates: list[dict[str, Any]] = []
    gate_ids: set[str] = set()
    for gate in policy["gates"]:
        if not isinstance(gate, dict):
            raise ValueError("gate_must_be_object")
        missing_gate = sorted(REQUIRED_GATE - gate.keys())
        if missing_gate:
            raise ValueError(f"missing_gate_fields:{','.join(missing_gate)}")
        gate_id = gate["gate_id"]
        if gate_id in gate_ids:
            raise ValueError(f"duplicate_gate:{gate_id}")
        gate_ids.add(gate_id)
        if gate["mode"] not in ALLOWED_MODES:
            raise ValueError(f"invalid_gate_mode:{gate_id}")
        if not isinstance(gate["rule_ids"], list) or not gate["rule_ids"]:
            raise ValueError(f"empty_gate:{gate_id}")
        for rule_id in gate["rule_ids"]:
            if rule_id not in rules:
                raise ValueError(f"unknown_rule:{gate_id}:{rule_id}")
        gates.append({"gate_id": gate_id, "rule_ids": sorted(gate["rule_ids"]), "mode": gate["mode"]})

    plan = {
        "plan_type": "P0-06-GATE-PLAN",
        "compiler_version": "1.0.0",
        "policy_id": policy["policy_id"],
        "policy_version": policy["policy_version"],
        "policy_fingerprint": actual,
        "lineage": policy["lineage"],
        "rules": [rules[k] for k in sorted(rules)],
        "gates": sorted(gates, key=lambda x: x["gate_id"]),
        "authority_effect": "NONE",
    }
    plan["plan_fingerprint"] = hashlib.sha256(canonical_json(plan)).hexdigest()
    return plan


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: compile_policy_gate.py POLICY.json", file=sys.stderr)
        return 2
    policy = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(compile_policy(policy), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
