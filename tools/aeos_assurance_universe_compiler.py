"""Deterministic compiler for the AEOS open-ended assurance address space.

This module enumerates assurance *addresses*, not evidence or truth. It deliberately
cannot promote an address to PASS/CERTIFIED and cannot create authority. Concrete
reality adapters and independent verifiers remain separate boundaries.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

LIFECYCLE: tuple[str, ...] = (
    "DECLARE", "IDENTIFY", "OBSERVE", "VALIDATE", "BIND", "VERIFY",
    "AUTHORIZE", "EXECUTE", "PROVE", "CERTIFY", "PROMOTE", "DEPLOY",
    "MONITOR", "RECOVER", "REPLAY", "REBASELINE",
)

# 100 reusable assurance families. These are intentionally orthogonal to the
# 120-domain global universe so one family can be applied across many domains.
ASSURANCE_FAMILIES: tuple[str, ...] = (
    "reality_integrity", "source_integrity", "identity_integrity", "authority_integrity",
    "capability_integrity", "scope_integrity", "intent_integrity", "state_integrity",
    "transition_integrity", "time_integrity", "causality_integrity", "evidence_integrity",
    "evidence_authenticity", "evidence_completeness", "evidence_consistency", "evidence_freshness",
    "evidence_independence", "evidence_sufficiency", "evidence_revocation", "evidence_dependency",
    "provenance_integrity", "provenance_continuity", "provenance_authenticity", "provenance_completeness",
    "hash_integrity", "canonicalization_integrity", "serialization_integrity", "schema_integrity",
    "semantic_integrity", "configuration_integrity", "environment_integrity", "toolchain_integrity",
    "execution_integrity", "workflow_integrity", "runner_integrity", "checkout_integrity",
    "build_integrity", "build_isolation", "build_reproducibility", "artifact_integrity",
    "artifact_continuity", "artifact_immutability", "artifact_promotion", "artifact_rollback",
    "package_integrity", "release_integrity", "deployment_integrity", "dependency_integrity",
    "dependency_provenance", "dependency_resolution", "dependency_substitution", "supply_chain_integrity",
    "test_integrity", "test_discovery_integrity", "oracle_integrity", "regression_integrity",
    "determinism_integrity", "coverage_integrity", "mutation_resistance", "fuzz_resistance",
    "property_integrity", "ci_integrity", "ci_replayability", "log_integrity", "status_integrity",
    "contract_integrity", "policy_integrity", "governance_integrity", "approval_integrity",
    "separation_of_duties", "delegation_integrity", "escalation_integrity", "lease_integrity",
    "queue_integrity", "scheduling_integrity", "concurrency_integrity", "toctou_integrity",
    "locking_integrity", "idempotency_integrity", "transaction_integrity", "dependency_graph_integrity",
    "causal_graph_integrity", "change_graph_integrity", "blast_radius_integrity", "counterfactual_integrity",
    "decision_replayability", "decision_stability", "decision_provenance", "risk_integrity",
    "recovery_integrity", "checkpoint_integrity", "self_healing_integrity", "agent_intent_integrity",
    "agent_authority_integrity", "agent_memory_integrity", "multi_agent_isolation", "human_override_integrity",
    "novelty_detection", "unknown_management", "bypass_resistance", "common_mode_resistance",
    "assurance_completeness", "assurance_of_assurance", "constitutional_integrity", "knowledge_lifecycle_integrity",
)

DIMENSIONS: tuple[str, ...] = (
    "actor", "object", "boundary", "state", "time", "evidence", "authority", "dependency",
    "environment", "action", "consequence", "confidence", "independence", "freshness", "reversibility",
    "blast_radius", "recoverability", "observability", "causality", "provenance", "policy_version",
    "contract_version", "source_sha", "artifact_sha", "test_manifest_sha", "workflow_sha", "runner_id",
    "toolchain_id", "runtime_id", "configuration_id", "dependency_lock", "builder_id", "invocation_id",
    "certificate_id", "verifier_id", "oracle_id", "certifier_id", "human_approval", "scope", "intent",
    "assumptions", "unknowns", "exceptions", "applicability", "authorization", "delegation", "lease",
    "queue", "concurrency", "lock", "transaction", "schema", "semantic_version", "serialization",
    "canonical_form", "hash", "signature", "timestamp", "causal_parent", "causal_child", "claim",
    "observation", "derivation", "assertion", "source_ref", "evidence_ref", "provenance_ref", "common_mode",
    "correlation_group", "search_scope", "search_method", "search_snapshot", "negative_result", "mutation_id",
    "canary_id", "bypass_surface", "recovery_point", "recovery_target", "rollback_target", "promotion_target",
    "deployment_target", "memory_ref", "prompt_ref", "tool_ref", "agent_ref", "tenant", "session",
    "release_ref", "main_sha", "coverage_snapshot", "assurance_debt_id", "expiry", "revocation", "novelty",
)

NEVER_PASS = frozenset({"NOT_OBSERVED", "UNKNOWN", "STALE", "CONFLICT", "UNCLASSIFIED", "QUARANTINED"})


@dataclass(frozen=True)
class AssuranceAddress:
    assertion_id: str
    domain_id: str
    family: str
    dimension: str
    lifecycle: str


def _slug(value: str) -> str:
    return value.upper().replace("-", "_")


def assertion_id(domain_id: str, family: str, dimension: str, lifecycle: str) -> str:
    raw = "|".join((domain_id, family, dimension, lifecycle))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"AX-{_slug(domain_id)}-{_slug(family)[:20]}-{_slug(dimension)[:20]}-{_slug(lifecycle)}-{digest}"


def compile_addresses(
    domain_ids: Iterable[str],
    families: Sequence[str] = ASSURANCE_FAMILIES,
    dimensions: Sequence[str] = DIMENSIONS,
    lifecycle: Sequence[str] = LIFECYCLE,
) -> tuple[AssuranceAddress, ...]:
    domains = tuple(domain_ids)
    if len(families) != 100:
        raise ValueError("assurance family catalog must contain exactly 100 entries")
    if len(dimensions) != 100:
        raise ValueError("assurance dimension catalog must contain exactly 100 entries")
    if len(set(families)) != len(families) or len(set(dimensions)) != len(dimensions):
        raise ValueError("catalog entries must be unique")
    if not domains or not all(isinstance(d, str) and d for d in domains):
        raise ValueError("domain ids must be non-empty strings")
    return tuple(
        AssuranceAddress(assertion_id(d, f, x, l), d, f, x, l)
        for d in domains for f in families for x in dimensions for l in lifecycle
    )


def compile_catalog(domain_ids: Iterable[str]) -> dict:
    domains = tuple(domain_ids)
    addresses = compile_addresses(domains)
    canonical = [a.__dict__ for a in addresses]
    digest = hashlib.sha256(json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "contract": "research-os-aeos-assurance-universe-100x/v1",
        "generated": True,
        "domain_count": len(domains),
        "family_count": len(ASSURANCE_FAMILIES),
        "dimension_count": len(DIMENSIONS),
        "lifecycle_count": len(LIFECYCLE),
        "address_count": len(addresses),
        "address_digest": digest,
        "never_pass": sorted(NEVER_PASS),
        "addresses": canonical,
    }


def validate_observation(record: Mapping[str, object]) -> None:
    state = record.get("state")
    if state in NEVER_PASS:
        raise ValueError(f"non-passing assurance state: {state}")
    if state not in {
        "NOT_APPLICABLE", "ASSERTED", "OBSERVED", "DERIVED", "SUPPORTED", "VALID", "INVALID",
        "VERIFIED", "INDEPENDENTLY_VERIFIED", "CERTIFIED", "PROMOTABLE", "PROMOTED",
        "DEPLOYED", "RECOVERED", "REVERIFIED",
    }:
        raise ValueError("unknown assurance state")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Compile AEOS assurance address space")
    parser.add_argument("--domains", nargs="+", required=True)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    catalog = compile_catalog(args.domains)
    if args.summary:
        print(json.dumps({k: catalog[k] for k in catalog if k != "addresses"}, sort_keys=True))
    else:
        print(json.dumps(catalog, sort_keys=True, indent=2))
