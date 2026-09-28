"""Executable AEOS 100x contract-conformance boundary.

The contract JSON is configuration, not executable verification. This module
loads the canonical contract and verifies the structural, semantic, and
boundary invariants required by the AEOS 100x contract. It never certifies
runtime state and never grants authority.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping


class ContractConformanceError(ValueError):
    """Raised when the AEOS 100x contract cannot be established as conformant."""


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "current" / "AEOS_100X_CONTRACT.json"
CONTRACT_ID = "research-os-aeos-100x/v1"
SHA40 = re.compile(r"^[0-9a-f]{40}$")

_REQUIRED_PRINCIPLES = {
    "detect_before_diagnose",
    "root_cause_before_fix",
    "evidence_before_certification",
    "provenance_before_trust",
    "independent_verification_before_integration",
    "main_verification_before_reanchor",
    "no_unknown_as_pass",
    "no_merge_as_repair",
    "no_governance_self_modification",
    "no_autonomous_stop_without_stop_proof",
    "declared_state_is_not_reality",
    "discovery_is_not_authorization",
    "merge_is_not_post_merge_health",
    "open_ended_assurance_must_not_expand_trust_anchors",
    "reality_observation_is_not_verification",
    "certificate_chain_integrity_is_not_subject_truth",
    "governance_proof_is_external_to_autonomous_execution",
    "complexity_may_grow_without_bound_but_trust_requires_proof",
    "freshness_is_explicit_and_replayable",
    "shared_sources_do_not_count_as_independent_evidence",
    "negative_space_requires_explicit_absence_evidence",
}

_REQUIRED_STATES = (
    "MISSION_CREATED", "CONTRACTED", "PLANNED", "QUEUED", "LEASED",
    "BRANCHED", "DOCUMENTED", "IMPLEMENTED", "DIFF_CAPTURED", "TESTED",
    "CI_VERIFIED", "FORENSIC_VERIFIED", "REGRESSION_VERIFIED",
    "EVIDENCE_VERIFIED", "PROVENANCE_VERIFIED", "AUTHORITY_VERIFIED",
    "CERTIFIED", "INTEGRATED", "MAIN_VERIFIED", "REANCHORED", "COMPLETED",
)

_REQUIRED_FAILURE_PROTOCOL = (
    "PRESERVE_FAILURE_EVIDENCE", "CLASSIFY", "REPRODUCE", "HYPOTHESIZE",
    "VERIFY_ROOT_CAUSE", "APPLY_SOURCE_FIX", "RETEST", "REGRESSION", "REVERIFY",
)

_REQUIRED_CERTIFICATE_CHAIN = (
    "OBSERVATION_CERTIFICATE", "VERIFICATION_CERTIFICATE", "ASSURANCE_CERTIFICATE",
    "INTEGRATION_CERTIFICATE", "MAIN_STATE_CERTIFICATE", "COMPLETION_CERTIFICATE",
)

_REQUIRED_BOUNDARIES = {
    "authority_risk", "semantic_diff", "blast_radius", "decision_replay",
    "post_merge_verification", "assurance_fabric", "runtime_certificate", "toctou",
    "main_reanchor", "reality_observation", "reality_scanner", "evidence_fabric",
    "certificate_chain", "constitutional_firewall", "temporal_freshness",
    "anti_circularity", "negative_space", "negative_space_scanner", "assurance_boundary",
}


def load_contract(path: Path = CONTRACT_PATH) -> Mapping[str, object]:
    """Load the canonical contract without accepting caller-supplied claims."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractConformanceError(f"contract_unreadable:{path}") from exc
    if not isinstance(payload, Mapping):
        raise ContractConformanceError("contract_root_must_be_object")
    return payload


def _require_sequence(payload: Mapping[str, object], key: str, expected: tuple[str, ...]) -> None:
    value = payload.get(key)
    if not isinstance(value, list) or tuple(value) != expected:
        raise ContractConformanceError(f"contract_{key}_mismatch")
    if len(set(value)) != len(value):
        raise ContractConformanceError(f"contract_{key}_not_unique")


def validate_contract(payload: Mapping[str, object] | None = None) -> Mapping[str, object]:
    """Verify canonical contract invariants and referenced executable boundaries."""
    contract = load_contract() if payload is None else payload
    if contract.get("contract") != CONTRACT_ID:
        raise ContractConformanceError("contract_id_mismatch")
    baseline = contract.get("baseline_sha")
    if not isinstance(baseline, str) or not SHA40.fullmatch(baseline):
        raise ContractConformanceError("contract_baseline_sha_invalid")
    if contract.get("mode") != "AUTO_GUARDED" or contract.get("auto_merge") is not False:
        raise ContractConformanceError("contract_execution_policy_mismatch")

    principles = contract.get("core_principles")
    if not isinstance(principles, list) or not _REQUIRED_PRINCIPLES.issubset(principles):
        raise ContractConformanceError("contract_core_principles_incomplete")
    _require_sequence(contract, "state_order", _REQUIRED_STATES)
    terminals = contract.get("terminal_states")
    if not isinstance(terminals, list) or set(terminals) != {"COMPLETED", "BLOCKED", "QUARANTINED", "CANCELLED"}:
        raise ContractConformanceError("contract_terminal_states_mismatch")
    _require_sequence(contract, "failure_protocol", _REQUIRED_FAILURE_PROTOCOL)
    _require_sequence(contract, "certificate_chain", _REQUIRED_CERTIFICATE_CHAIN)

    stop = contract.get("stop_requirements")
    required_stop = {
        "required_queue": 0,
        "recovery_queue": 0,
        "unresolved_failures": 0,
        "unknown": 0,
        "stale": 0,
        "unverified_changes": 0,
        "blocked_required_dependencies": 0,
        "uncertified_integrations": 0,
        "main_verified": True,
        "stop_proof": "PASS",
    }
    if not isinstance(stop, Mapping) or dict(stop) != required_stop:
        raise ContractConformanceError("contract_stop_requirements_mismatch")

    authority = contract.get("authority")
    required_authority = {
        "planner": "bounded",
        "builder": "bounded",
        "verifier": "independent",
        "certifier": "governed",
        "merge": "outside_self_evaluation",
        "constitution_mutation": False,
        "policy_self_weakening": False,
    }
    if not isinstance(authority, Mapping) or dict(authority) != required_authority:
        raise ContractConformanceError("contract_authority_mismatch")

    boundaries = contract.get("boundaries")
    if not isinstance(boundaries, Mapping) or set(boundaries) != _REQUIRED_BOUNDARIES:
        raise ContractConformanceError("contract_boundaries_incomplete")
    for name, relative in boundaries.items():
        if not isinstance(relative, str) or not relative.endswith(".py"):
            raise ContractConformanceError(f"contract_boundary_not_executable:{name}")
        path = ROOT / relative
        if not path.is_file():
            raise ContractConformanceError(f"contract_boundary_missing:{name}:{relative}")

    if contract.get("reality_rule") != "DECLARED -> OBSERVED -> EVIDENCE_BOUND -> INDEPENDENTLY_VERIFIED -> ASSURED -> CERTIFIED":
        raise ContractConformanceError("contract_reality_rule_mismatch")
    if contract.get("freshness_rule") != "observed_at + explicit_reference_time + bounded_max_age -> FRESH|STALE|CONFLICT":
        raise ContractConformanceError("contract_freshness_rule_mismatch")
    if contract.get("independence_rule") != "distinct verifier identity + no undisclosed common source + evidence source not equal subject source":
        raise ContractConformanceError("contract_independence_rule_mismatch")
    if contract.get("negative_space_rule") != "absence of unresolved failures, unknowns, stale evidence, orphan work, unauthorized mutation, and uncertified integration must be evidenced before completion":
        raise ContractConformanceError("contract_negative_space_rule_mismatch")

    budgets = contract.get("budgets")
    required_budgets = {
        "max_retry_without_new_evidence": 0,
        "max_concurrent_high_risk": 1,
        "lease_required": True,
        "change_budget_required": True,
        "recovery_point_required_for_irreversible_action": True,
    }
    if not isinstance(budgets, Mapping) or dict(budgets) != required_budgets:
        raise ContractConformanceError("contract_budgets_mismatch")
    return contract


def contract_conformance() -> bool:
    """Return True only when the canonical contract satisfies all invariants."""
    validate_contract()
    return True
