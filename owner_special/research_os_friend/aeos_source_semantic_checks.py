"""Source-level semantic checks for AEOS assurance boundaries."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]


class SourceSemanticCheckError(ValueError):
    """Raised when a target implementation cannot be inspected safely."""


def _source(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        raise SourceSemanticCheckError(f"missing_source:{relative}")
    return path.read_text(encoding="utf-8")


def _tree(relative: str) -> ast.AST:
    try:
        return ast.parse(_source(relative), filename=relative)
    except SyntaxError as exc:
        raise SourceSemanticCheckError(f"syntax_error:{relative}:{exc}") from exc


def _names(tree: ast.AST) -> set[str]:
    return {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}


def _semantic(relative: str, *, symbols: Iterable[str] = (), constructs: Iterable[str] = ()) -> bool:
    source = _source(relative)
    return set(symbols).issubset(_names(_tree(relative))) and all(token in source for token in constructs)


def _has_attribute_comparison(
    tree: ast.AST,
    *,
    left_attribute: str,
    operator: type[ast.cmpop],
    right_attribute: str,
) -> bool:
    """Find an attribute-to-attribute comparison without depending on source formatting."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1 or len(node.comparators) != 1:
            continue
        left = node.left
        right = node.comparators[0]
        if (
            isinstance(node.ops[0], operator)
            and isinstance(left, ast.Attribute)
            and isinstance(right, ast.Attribute)
            and left.attr == left_attribute
            and right.attr == right_attribute
        ):
            return True
    return False


def dependency_integrity() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_durable_work_graph.py", symbols=("WorkGraph", "WorkItem"), constructs=("_assert_acyclic", "dependency cycle", "self dependency"))


def dependency_provenance() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_durable_work_graph.py", symbols=("WorkItem", "WorkGraph"), constructs=("evidence_refs", "baseline_sha", "VERIFYING", "CERTIFYING"))


def deterministic_ordering() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_durable_work_graph.py", symbols=("WorkGraph",), constructs=("def ready", "sorted(", "dependencies_satisfied"))


def lease_expiry() -> bool:
    return _semantic("owner_special/research_os_friend/autonomous_workloop.py", symbols=("WorkItem",), constructs=("lease_id", "LEASED", "lease mismatch"))


def idempotency() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_durable_work_graph.py", symbols=("WorkGraph",), constructs=("terminal work item is immutable", "duplicate work_id"))


def rollback_readiness() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_recovery_fabric.py", symbols=("RecoveryCheckpoint", "validate_rollback_request"), constructs=("reversible", "observed SHA does not match checkpoint baseline", "evidence does not exactly match checkpoint evidence"))


def state_reconstruction() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_recovery_fabric.py", symbols=("create_checkpoint",), constructs=("state_digest", "_digest", "checkpoint_id"))


def disaster_recovery() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_recovery_fabric.py", symbols=("RecoveryCheckpoint", "validate_rollback_request"), constructs=("reversible", "baseline_sha", "rollback"))


def failure_fingerprint() -> bool:
    return _semantic("owner_special/research_os_friend/autonomous_workloop.py", symbols=("WorkItem",), constructs=("failure_fingerprint", "hashlib.sha256", "failure_class", "evidence_refs"))


def failure_lineage() -> bool:
    return _semantic("owner_special/research_os_friend/autonomous_workloop.py", symbols=("WorkItem",), constructs=("failure_class", "evidence_refs", "failure_fingerprint"))


def regression_memory() -> bool:
    return _semantic("owner_special/research_os_friend/autonomous_workloop.py", symbols=("WorkItem",), constructs=("attempt_count", "failure_fingerprint", "QUARANTINED"))


def root_cause_reintroduction() -> bool:
    return _semantic("owner_special/research_os_friend/autonomous_workloop.py", symbols=("WorkItem",), constructs=("failure", "attempt_count", "failure_fingerprint"))


def identity_continuity() -> bool:
    return _semantic("owner_special/research_os_friend/identity_foundation.py", constructs=("sha256", "lineage", "verify"))


def delegation_chain() -> bool:
    return _semantic("tools/validate_identity_authority.py", symbols=("scope_subset", "validate"), constructs=("delegation_scope_escalation", "self_delegation", "inactive_delegator", "unknown_delegatee", "valid_until"))


def confused_deputy() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_authority_risk.py", constructs=("authority", "capability", "identity"))


def capability_boundary() -> bool:
    return _semantic("owner_special/research_os_friend/capabilities.py", constructs=("capability", "permission"))


def policy_monotonicity() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("PolicySnapshot", "policy_monotonicity"), constructs=("version + 1", "issubset", "deny_rules"))


def agent_loop_safety() -> bool:
    return _semantic("owner_special/research_os_friend/autonomous_workloop.py", symbols=("WorkItem",), constructs=("attempt_count", "QUARANTINED", "terminal state cannot transition"))


def retry_new_evidence() -> bool:
    return _semantic("owner_special/research_os_friend/autonomous_workloop.py", symbols=("WorkItem",), constructs=("failure", "evidence_refs", "attempt_count"))


def tool_trust_boundary() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_authority_risk.py", constructs=("evidence", "authority", "policy"))


def instruction_boundary() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_authority_risk.py", constructs=("authority", "policy", "evidence"))


def model_version_drift() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("ModelVersion", "detect_model_version_drift", "model_version_drift"), constructs=("expected != observed", "provider", "model", "version"))


def distributed_lock() -> bool:
    return _semantic("owner_special/research_os_friend/autonomous_workloop.py", constructs=("lease_id", "lease mismatch"))


def no_evidence_as_authority() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_authority_risk.py", constructs=("authority", "evidence", "independent"))


def no_merge_as_repair() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("no_merge_as_repair",), constructs=("unresolved_failures", "repair_in_progress", "merge_requested"))


def no_self_merge() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("no_self_merge",), constructs=("actor != source_owner", "merge identities"))


def evidence_coverage() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_evidence_fabric.py", constructs=("evidence", "coverage", "reference"))


def evidence_tamper() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("evidence_tamper",), constructs=("original_digest == observed_digest", "len(observed_digest) == 64"))


def evidence_conflict() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("evidence_conflict",), constructs=("len(set(digests)) > 1", "len(digests) > 0"))


def evidence_revocation() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("evidence_revocation",), constructs=("type(revoked) is bool", "return", "revoked"))


def audit_chain_integrity() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("AuditEntry", "audit_chain_integrity"), constructs=("previous_digest", "compute_digest", "entry.sequence != expected_sequence"))


def audit_completeness() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("audit_completeness",), constructs=("required_sequences", "actual == list(required_sequences)", "audit_chain_integrity"))


def assurance_coverage() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_assurance_check_fabric.py", symbols=("validate_registry", "validate_report"), constructs=("required = [item[\"id\"] for item in registry[\"checks\"]]", "set(checks) != set(required)"))


def blind_spot_discovery() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_negative_space_scanner.py", symbols=("InventoryItem", "scan_observed_inventory"), constructs=("unknown inventory kind", "forbidden_states", "scan_negative_space"))


def semantic_compatibility() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("SchemaProfile", "semantic_compatibility"), constructs=("new.version < old.version", "new.fields[name] != old_type", "new.defaults"))


def version_monotonicity() -> bool:
    return _semantic("owner_special/research_os_friend/self_learning/provenance.py", symbols=("SkillProvenanceLedger",), constructs=("previous.version + 1", "parent_version != previous.version", "provenance versions must be contiguous"))


def backward_compatibility() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("SchemaProfile", "backward_compatibility"), constructs=("return semantic_compatibility(old, new)",))


def forward_compatibility() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("SchemaProfile", "forward_compatibility"), constructs=("name in old.fields or name in new.defaults",))


def migration_safety() -> bool:
    relative = "owner_special/research_os_friend/aeos_integrity_boundaries.py"
    tree = _tree(relative)
    return (
        {"MigrationPlan", "migration_safety"}.issubset(_names(tree))
        and _has_attribute_comparison(
            tree,
            left_attribute="target_version",
            operator=ast.LtE,
            right_attribute="source_version",
        )
        and all(token in _source(relative) for token in ("preconditions", "postconditions", "reversible"))
    )


def rollback_migration() -> bool:
    return _semantic("owner_special/research_os_friend/aeos_integrity_boundaries.py", symbols=("MigrationPlan", "rollback_migration"), constructs=("observed_version == plan.target_version", "observed_digest == plan.target_digest", "rollback_target == plan.source_version"))


_CHECKS = {name for name, value in globals().items() if callable(value) and not name.startswith("_") and name not in {"Iterable", "Path"}}


def evaluate(check_id: str) -> bool:
    """Evaluate a named source-semantic check against executable source."""
    name = check_id.lower()
    fn = globals().get(name)
    if not callable(fn) or name not in _CHECKS:
        raise SourceSemanticCheckError(f"unknown_source_semantic_check:{check_id}")
    return bool(fn())
