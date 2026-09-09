#!/usr/bin/env python3
"""Independent, fail-closed P0-05 provenance verifier."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
HEX_RE = re.compile(r"^[0-9a-f]+$")
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DOMAIN = b"provenance-entry-v1\x00"


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


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: object) -> str:
    return hashlib.sha256(DOMAIN + canonical_json(value).encode("utf-8")).hexdigest()


def plain_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def required(obj: dict, fields: list[str], prefix: str, errors: list[str]) -> None:
    for field in fields:
        if field not in obj:
            errors.append(f"missing:{prefix}.{field}")


def timestamp(value: object, field: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not ISO_RE.fullmatch(value):
        errors.append(f"invalid_timestamp:{field}")
        return
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"invalid_timestamp:{field}")


def validate_hash_record(record: object, entry_id: object, field: str, errors: list[str], allowed: set[str]) -> None:
    if not isinstance(record, dict):
        errors.append(f"invalid_hash_record:{entry_id}:{field}")
        return
    if set(record) != {"algorithm", "digest", "subject"}:
        errors.append(f"invalid_hash_identity:{entry_id}:{field}")
        return
    algorithm, value, subject = record["algorithm"], record["digest"], record["subject"]
    if algorithm not in allowed:
        errors.append(f"unsupported_algorithm:{entry_id}:{field}:{algorithm}")
        return
    if not isinstance(value, str) or not HEX_RE.fullmatch(value):
        errors.append(f"invalid_hash:{entry_id}:{field}")
        return
    if algorithm == "sha256" and not SHA256_RE.fullmatch(value):
        errors.append(f"invalid_sha256:{entry_id}:{field}")
    if algorithm == "git-sha1" and not SHA1_RE.fullmatch(value):
        errors.append(f"invalid_git_sha1:{entry_id}:{field}")
    if algorithm == "git-sha1" and subject not in {"git-commit", "git-blob"}:
        errors.append(f"git_sha1_wrong_identity:{entry_id}:{field}")
    if algorithm == "sha256" and subject in {"git-commit", "git-blob"}:
        errors.append(f"git_identity_requires_git_sha1:{entry_id}:{field}")


def validate(contract: dict, ledger: dict, target_commit: str | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(contract, dict) or contract.get("status") != "CANONICAL":
        return ["contract_not_canonical"]
    if not SEMVER_RE.fullmatch(str(contract.get("version", ""))):
        return ["invalid_contract_version"]
    if not isinstance(ledger, dict):
        return ["ledger_not_object"]
    if ledger.get("contract_version") != contract.get("version"):
        errors.append("ledger_contract_version_mismatch")
    entries = ledger.get("entries")
    if not isinstance(entries, list):
        return ["entries_collection_missing"]
    schema = contract.get("ledger", {})
    required_fields = schema.get("required_entry_fields", [])
    evidence_types = set(schema.get("evidence_types", []))
    allowed_algorithms = set(schema.get("supported_algorithms", []))
    if schema.get("hash_algorithm") != "sha256":
        errors.append("unsupported_primary_hash_algorithm")
    if "sha256" not in allowed_algorithms:
        errors.append("sha256_missing_from_algorithm_allowlist")
    entry_ids: set[str] = set()
    attestation_ids: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"entry[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"entry_not_object:{index}")
            continue
        required(entry, required_fields, prefix, errors)
        ident = entry.get("entry_id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"invalid_entry_id:{index}")
            ident = str(ident)
        elif ident in entry_ids:
            errors.append(f"duplicate_entry_id:{ident}")
        entry_ids.add(ident)
        if entry.get("sequence") != index + 1:
            errors.append(f"invalid_sequence:{ident}")
        timestamp(entry.get("recorded_at"), f"{prefix}.recorded_at", errors)
        for hash_field in ("input_hashes", "output_hashes"):
            hashes = entry.get(hash_field)
            if not isinstance(hashes, dict) or not hashes:
                errors.append(f"invalid_{hash_field}:{ident}")
            else:
                for name, record in hashes.items():
                    validate_hash_record(record, ident, f"{hash_field}.{name}", errors, allowed_algorithms)
        if entry.get("evidence_type") not in evidence_types:
            errors.append(f"unknown_evidence_type:{ident}")
        if index == 0:
            if entry.get("previous_entry_hash") is not None:
                errors.append(f"first_previous_hash_not_null:{ident}")
        elif entry.get("previous_entry_hash") != entries[index - 1].get("entry_hash"):
            errors.append(f"previous_hash_mismatch:{ident}")
        supplied_hash = entry.get("entry_hash")
        unsigned = dict(entry)
        unsigned.pop("entry_hash", None)
        if not isinstance(supplied_hash, str) or not SHA256_RE.fullmatch(supplied_hash):
            errors.append(f"invalid_entry_hash:{ident}")
        elif supplied_hash != digest(unsigned):
            errors.append(f"entry_hash_mismatch:{ident}")
        evidence = entry.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"evidence_not_object:{ident}")
            continue
        if entry.get("evidence_type") == "change":
            for field in ("source_commit", "target_commit", "evidence_ids", "attestation_id"):
                if not evidence.get(field):
                    errors.append(f"missing_{field}:{ident}")
            source = evidence.get("source_commit")
            target = evidence.get("target_commit")
            if isinstance(source, str) and not SHA1_RE.fullmatch(source):
                errors.append(f"invalid_source_commit:{ident}")
            if isinstance(target, str) and not SHA1_RE.fullmatch(target):
                errors.append(f"invalid_target_commit:{ident}")
            if target_commit and target != target_commit:
                errors.append(f"target_commit_mismatch:{ident}")
        elif entry.get("evidence_type") == "attestation":
            required(evidence, contract["attestation"]["required_fields"], f"{prefix}.evidence", errors)
            if evidence.get("attestation_id"):
                attestation_ids.add(evidence["attestation_id"])
            timestamp(evidence.get("issued_at"), f"{prefix}.evidence.issued_at", errors)
    if entries and entries[0].get("sequence") != schema.get("sequence_must_start_at", 1):
        errors.append("sequence_start_mismatch")
    if schema.get("sequence_must_be_contiguous"):
        expected = list(range(1, len(entries) + 1))
        actual = [e.get("sequence") for e in entries if isinstance(e, dict)]
        if actual != expected:
            errors.append("sequence_not_contiguous")
    evidence_index = {e.get("entry_id"): e for e in entries if isinstance(e, dict)}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("evidence"), dict):
            continue
        evidence = entry["evidence"]
        refs = evidence.get("evidence_ids", [])
        if not isinstance(refs, list) or any(ref not in evidence_index for ref in refs):
            errors.append(f"unknown_evidence_reference:{entry.get('entry_id')}")
        att_id = evidence.get("attestation_id")
        if att_id and att_id not in attestation_ids:
            errors.append(f"unknown_attestation_reference:{entry.get('entry_id')}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="current/PROVENANCE_EVIDENCE_CONTRACT.json")
    parser.add_argument("--ledger", default="current/PROVENANCE_EVIDENCE_LEDGER_FIXTURE.json")
    parser.add_argument("--target-commit", default=None)
    args = parser.parse_args()
    contract_path, ledger_path = Path(args.contract), Path(args.ledger)
    if not contract_path.is_absolute(): contract_path = Path.cwd() / contract_path
    if not ledger_path.is_absolute(): ledger_path = Path.cwd() / ledger_path
    errors: list[str] = []
    contract, ledger = load_json(contract_path, errors), load_json(ledger_path, errors)
    if contract is not None and ledger is not None:
        errors.extend(validate(contract, ledger, args.target_commit))
        if isinstance(ledger, dict):
            for entry in ledger.get("entries", []):
                if not isinstance(entry, dict):
                    continue
                for name, record in entry.get("output_hashes", {}).items() if isinstance(entry.get("output_hashes"), dict) else []:
                    if isinstance(record, dict) and record.get("algorithm") == "sha256" and str(record.get("subject", "")).startswith("artifact:"):
                        rel = record["subject"][len("artifact:"):]
                        artifact = (ROOT / rel).resolve()
                        if artifact.exists() and artifact.is_file():
                            actual = plain_sha256(json.loads(artifact.read_text(encoding="utf-8")))
                            if actual != record.get("digest"):
                                errors.append(f"derived_digest_mismatch:{entry.get('entry_id')}:{name}")
    report = {"status": "PASS" if not errors else "FAIL", "contract": display_path(contract_path), "ledger": display_path(ledger_path), "entry_count": len(ledger.get("entries", [])) if isinstance(ledger, dict) else 0, "errors": errors}
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
