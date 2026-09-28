#!/usr/bin/env python3
"""Fail-closed validator for the Universal Learning Root contract."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


REQUIRED_KNOWLEDGE_KINDS = {
    "FACT", "OBSERVATION", "MEASUREMENT", "MODEL", "HYPOTHESIS",
    "THEORY", "INTERPRETATION", "OPINION", "IDEA", "FICTION",
    "SIMULATION", "UNKNOWN",
}
REQUIRED_DOMAINS = {
    "LANGUAGE", "MATHEMATICS", "SCIENCE", "ENGINEERING", "TECHNOLOGY",
    "ARTS", "DESIGN", "BUSINESS", "ECONOMICS", "LAW", "HUMANITIES",
    "SOCIAL_SCIENCE", "EDUCATION", "LIFE_AND_WORK", "RESEARCH",
}
REQUIRED_PRINCIPLES = {
    "understand_before_act",
    "unknown_is_not_known",
    "evidence_before_confidence",
    "confidence_is_not_truth",
    "learning_does_not_grant_authority",
    "contradictions_are_preserved_until_resolved",
    "supersession_preserves_history",
    "interruption_preserves_recovery_state",
    "cross_domain_transfer_requires_validation",
    "self_correction_requires_retest",
    "human_correction_is_lineage_bearing",
    "no_unauthorized_self_modification",
}


def validate(contract: dict) -> str:
    if contract.get("contract_id") != "research-os-universal-learning-v1":
        raise ValueError("invalid contract_id")
    if contract.get("version") != 1:
        raise ValueError("unsupported contract version")

    root = contract.get("mathematical_root", {})
    if root.get("symbol") != "10^1000":
        raise ValueError("mathematical root mismatch")
    if root.get("materialization") != "forbidden":
        raise ValueError("10^1000 materialization must be forbidden")
    if root.get("execution") != "bounded_projection":
        raise ValueError("execution must be bounded projection")

    if set(contract.get("knowledge_kinds", ())) != REQUIRED_KNOWLEDGE_KINDS:
        raise ValueError("knowledge kind set mismatch")
    if set(contract.get("domains", ())) != REQUIRED_DOMAINS:
        raise ValueError("domain set mismatch")
    if not REQUIRED_PRINCIPLES.issubset(set(contract.get("principles", ()))):
        raise ValueError("required learning principles missing")

    lineage = set(contract.get("required_lineage", ()))
    for item in ("purpose", "intent", "requirement", "scope", "context",
                 "source", "assumption", "learning_event", "test",
                 "evidence", "confidence"):
        if item not in lineage:
            raise ValueError(f"missing lineage field: {item}")

    authority = contract.get("authority", {})
    if authority.get("merge_authority") != "unchanged":
        raise ValueError("merge authority boundary changed")

    resources = contract.get("resource_policy", {})
    if resources.get("unbounded_execution") != "forbidden":
        raise ValueError("unbounded execution must be forbidden")

    canonical = json.dumps(contract, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="current/UNIVERSAL_LEARNING_CONTRACT.json")
    args = parser.parse_args()
    try:
        contract = json.loads(Path(args.contract).read_text(encoding="utf-8"))
        fingerprint = validate(contract)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print("PASS: UNIVERSAL_LEARNING_CONTRACT")
    print(f"contract_sha256: {fingerprint}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
