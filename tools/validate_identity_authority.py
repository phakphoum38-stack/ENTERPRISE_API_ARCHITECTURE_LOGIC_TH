#!/usr/bin/env python3
"""Validate the canonical P0-04 identity and authority fixture fail-closed."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path, errors: list[str]):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"cannot_load_json:{display_path(path)}:{exc}")
        return None


def required(obj: dict, fields: list[str], prefix: str, errors: list[str]) -> None:
    for field in fields:
        if field not in obj:
            errors.append(f"missing:{prefix}.{field}")


def timestamp(value, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not ISO_RE.fullmatch(value):
        errors.append(f"invalid_timestamp:{field}")
        return
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo != timezone.utc:
            errors.append(f"timestamp_not_utc:{field}")
    except ValueError:
        errors.append(f"invalid_timestamp:{field}")


def ids_unique(items: list[dict], kind: str, errors: list[str]) -> None:
    seen: set[str] = set()
    for item in items:
        ident = item.get("id")
        if ident in seen:
            errors.append(f"duplicate_{kind}_id:{ident}")
        seen.add(ident)


def scope_subset(child: dict, parent: dict) -> bool:
    return all(key in parent and parent[key] == value for key, value in child.items())


def validate(contract: dict, fixture: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict):
        return ["contract_not_object"]
    if contract.get("status") != "CANONICAL":
        errors.append("contract_not_canonical")
    if not SEMVER_RE.fullmatch(str(contract.get("version", ""))):
        errors.append("invalid_contract_version")

    identities = fixture.get("identities") if isinstance(fixture, dict) else None
    capabilities = fixture.get("capabilities") if isinstance(fixture, dict) else None
    grants = fixture.get("grants") if isinstance(fixture, dict) else None
    delegations = fixture.get("delegations") if isinstance(fixture, dict) else None
    revocations = fixture.get("revocations") if isinstance(fixture, dict) else None
    proofs = fixture.get("authorization_proofs") if isinstance(fixture, dict) else None
    collections = [(identities, "identity"), (capabilities, "capability"), (grants, "grant"),
                   (delegations, "delegation"), (revocations, "revocation"), (proofs, "proof")]
    for items, kind in collections:
        if not isinstance(items, list):
            errors.append(f"{kind}_collection_missing")
        else:
            ids_unique(items, kind, errors)

    identity_map = {x.get("id"): x for x in identities or []}
    capability_map = {x.get("id"): x for x in capabilities or []}
    grant_map = {x.get("id"): x for x in grants or []}
    delegation_map = {x.get("id"): x for x in delegations or []}
    revoked_subjects = {x.get("subject_id") for x in revocations or []}

    for identity in identities or []:
        required(identity, ["id", "type", "status", "created_at", "issuer"], "identity", errors)
        if identity.get("type") not in contract.get("identity_types", []):
            errors.append(f"unknown_identity_type:{identity.get('id')}")
        if identity.get("status") not in contract["identity_requirements"]["statuses"]:
            errors.append(f"invalid_identity_status:{identity.get('id')}")
        timestamp(identity.get("created_at"), f"identity:{identity.get('id')}.created_at", errors)
        if identity.get("status") == "revoked" and identity.get("id") not in revoked_subjects:
            errors.append(f"revoked_identity_missing_revocation:{identity.get('id')}")

    for cap in capabilities or []:
        required(cap, ["id", "action", "resource", "scope", "risk_class"], "capability", errors)
        if cap.get("risk_class") not in contract["capability_schema"]["risk_classes"]:
            errors.append(f"invalid_risk_class:{cap.get('id')}")
        if not isinstance(cap.get("scope"), dict) or not cap.get("scope"):
            errors.append(f"missing_capability_scope:{cap.get('id')}")
        if isinstance(cap.get("scope"), dict) and any(v == "*" for v in cap["scope"].values()):
            errors.append(f"wildcard_scope:{cap.get('id')}")

    for grant in grants or []:
        required(grant, ["id", "subject_id", "capability_id", "scope", "granted_by", "valid_from", "status"], "grant", errors)
        if grant.get("subject_id") not in identity_map:
            errors.append(f"unknown_grant_subject:{grant.get('id')}")
        if grant.get("capability_id") not in capability_map:
            errors.append(f"unknown_grant_capability:{grant.get('id')}")
        if grant.get("granted_by") not in identity_map:
            errors.append(f"unknown_grantor:{grant.get('id')}")
        if grant.get("subject_id") == grant.get("granted_by"):
            errors.append(f"self_grant:{grant.get('id')}")
        if identity_map.get(grant.get("granted_by"), {}).get("status") != "active":
            errors.append(f"inactive_grantor:{grant.get('id')}")
        if identity_map.get(grant.get("subject_id"), {}).get("status") == "revoked":
            errors.append(f"grant_to_revoked_identity:{grant.get('id')}")
        if grant.get("status") not in contract["grant_schema"]["statuses"]:
            errors.append(f"invalid_grant_status:{grant.get('id')}")
        timestamp(grant.get("valid_from"), f"grant:{grant.get('id')}.valid_from", errors)
        cap = capability_map.get(grant.get("capability_id"))
        if cap and isinstance(grant.get("scope"), dict) and not scope_subset(grant["scope"], cap.get("scope", {})):
            errors.append(f"grant_scope_escalation:{grant.get('id')}")

    for delegation in delegations or []:
        required(delegation, ["id", "delegator_id", "delegatee_id", "capability_id", "scope", "valid_from", "valid_until", "status"], "delegation", errors)
        if delegation.get("delegator_id") == delegation.get("delegatee_id"):
            errors.append(f"self_delegation:{delegation.get('id')}")
        if identity_map.get(delegation.get("delegator_id"), {}).get("status") != "active":
            errors.append(f"inactive_delegator:{delegation.get('id')}")
        if delegation.get("delegator_id") in revoked_subjects:
            errors.append(f"revoked_delegator:{delegation.get('id')}")
        if delegation.get("delegatee_id") not in identity_map:
            errors.append(f"unknown_delegatee:{delegation.get('id')}")
        if delegation.get("capability_id") not in capability_map:
            errors.append(f"unknown_delegation_capability:{delegation.get('id')}")
        if delegation.get("status") not in contract["delegation_schema"]["status_values"]:
            errors.append(f"invalid_delegation_status:{delegation.get('id')}")
        timestamp(delegation.get("valid_from"), f"delegation:{delegation.get('id')}.valid_from", errors)
        timestamp(delegation.get("valid_until"), f"delegation:{delegation.get('id')}.valid_until", errors)
        if isinstance(delegation.get("valid_from"), str) and isinstance(delegation.get("valid_until"), str) and delegation["valid_until"] <= delegation["valid_from"]:
            errors.append(f"invalid_delegation_window:{delegation.get('id')}")
        cap = capability_map.get(delegation.get("capability_id"))
        if cap and isinstance(delegation.get("scope"), dict) and not scope_subset(delegation["scope"], cap.get("scope", {})):
            errors.append(f"delegation_scope_escalation:{delegation.get('id')}")

    for rev in revocations or []:
        required(rev, ["id", "subject_id", "reason", "revoked_by", "revoked_at"], "revocation", errors)
        if rev.get("subject_id") not in identity_map:
            errors.append(f"unknown_revocation_subject:{rev.get('id')}")
        if identity_map.get(rev.get("revoked_by"), {}).get("status") != "active":
            errors.append(f"inactive_revoker:{rev.get('id')}")
        timestamp(rev.get("revoked_at"), f"revocation:{rev.get('id')}.revoked_at", errors)

    active_grants = {g["id"]: g for g in grants or [] if g.get("status") == "active" and g.get("subject_id") not in revoked_subjects}
    for proof in proofs or []:
        required(proof, ["proof_id", "request_id", "subject_id", "capability_id", "resource", "action", "scope", "decision", "checked_at", "policy_version"], "proof", errors)
        if proof.get("decision") not in contract["authorization_proof"]["decisions"]:
            errors.append(f"invalid_proof_decision:{proof.get('proof_id')}")
        if proof.get("subject_id") not in identity_map:
            errors.append(f"unknown_proof_subject:{proof.get('proof_id')}")
        elif identity_map[proof["subject_id"]].get("status") != "active":
            errors.append(f"inactive_proof_subject:{proof.get('proof_id')}")
        if proof.get("capability_id") not in capability_map:
            errors.append(f"unknown_proof_capability:{proof.get('proof_id')}")
        matching = [g for g in active_grants.values() if g.get("subject_id") == proof.get("subject_id") and g.get("capability_id") == proof.get("capability_id")]
        if proof.get("decision") == "ALLOW" and not matching:
            errors.append(f"allow_without_active_grant:{proof.get('proof_id')}")
        if matching and proof.get("decision") == "ALLOW":
            if not any(scope_subset(proof.get("scope", {}), g.get("scope", {})) for g in matching):
                errors.append(f"proof_scope_exceeds_grant:{proof.get('proof_id')}")
        timestamp(proof.get("checked_at"), f"proof:{proof.get('proof_id')}.checked_at", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="current/IDENTITY_AUTHORITY_CONTRACT.json")
    parser.add_argument("--fixture", default="current/IDENTITY_AUTHORITY_FIXTURE.json")
    args = parser.parse_args()
    contract_path = Path(args.contract)
    fixture_path = Path(args.fixture)
    if not contract_path.is_absolute():
        contract_path = Path.cwd() / contract_path
    if not fixture_path.is_absolute():
        fixture_path = Path.cwd() / fixture_path
    errors: list[str] = []
    contract = load_json(contract_path, errors)
    fixture = load_json(fixture_path, errors)
    if contract is not None and fixture is not None:
        errors.extend(validate(contract, fixture))
    report = {
        "status": "PASS" if not errors else "FAIL",
        "contract": display_path(contract_path),
        "fixture": display_path(fixture_path),
        "identity_count": len(fixture.get("identities", [])) if isinstance(fixture, dict) else 0,
        "capability_count": len(fixture.get("capabilities", [])) if isinstance(fixture, dict) else 0,
        "grant_count": len(fixture.get("grants", [])) if isinstance(fixture, dict) else 0,
        "proof_count": len(fixture.get("authorization_proofs", [])) if isinstance(fixture, dict) else 0,
        "errors": errors,
    }
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
