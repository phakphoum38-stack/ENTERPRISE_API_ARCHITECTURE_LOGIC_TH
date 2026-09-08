#!/usr/bin/env python3
"""Validate the P0-05 provenance ledger, including its tamper-evident hash chain."""
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
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

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

def validate(contract: dict, ledger: dict) -> list[str]:
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
    schema = contract["ledger"]
    required_fields = schema["required_entry_fields"]
    evidence_types = set(schema["evidence_types"])
    entry_ids: set[str] = set()
    attestation_ids: set[str] = set()
    for index, entry in enumerate(entries):
        prefix = f"entry[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"entry_not_object:{index}")
            continue
        required(entry, required_fields, prefix, errors)
        ident = entry.get("entry_id")
        if ident in entry_ids:
            errors.append(f"duplicate_entry_id:{ident}")
        entry_ids.add(ident)
        seq = entry.get("sequence")
        if seq != index + 1:
            errors.append(f"invalid_sequence:{ident}")
        timestamp(entry.get("recorded_at"), f"{prefix}.recorded_at", errors)
        for hash_field in ("input_hashes", "output_hashes"):
            hashes = entry.get(hash_field)
            if not isinstance(hashes, dict):
                errors.append(f"invalid_{hash_field}:{ident}")
            else:
                for name, value in hashes.items():
                    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
                        errors.append(f"invalid_hash:{ident}:{hash_field}.{name}")
        if entry.get("evidence_type") not in evidence_types:
            errors.append(f"unknown_evidence_type:{ident}")
        if index == 0:
            if entry.get("previous_entry_hash") is not None:
                errors.append(f"first_previous_hash_not_null:{ident}")
        elif entry.get("previous_entry_hash") != entries[index - 1].get("entry_hash"):
            errors.append(f"previous_hash_mismatch:{ident}")
        supplied_hash = entry.get("entry_hash")
        unsigned = dict(entry); unsigned.pop("entry_hash", None)
        if not isinstance(supplied_hash, str) or not SHA256_RE.fullmatch(supplied_hash):
            errors.append(f"invalid_entry_hash:{ident}")
        elif supplied_hash != digest(unsigned):
            errors.append(f"entry_hash_mismatch:{ident}")
        evidence = entry.get("evidence")
        if not isinstance(evidence, dict):
            errors.append(f"evidence_not_object:{ident}")
        elif entry.get("evidence_type") == "change":
            if not evidence.get("source_commit"):
                errors.append(f"missing_source_commit:{ident}")
            if not evidence.get("evidence_ids"):
                errors.append(f"missing_evidence_ids:{ident}")
            if not evidence.get("attestation_id"):
                errors.append(f"missing_attestation_id:{ident}")
        elif entry.get("evidence_type") == "attestation":
            required(evidence, contract["attestation"]["required_fields"], f"{prefix}.evidence", errors)
            if evidence.get("attestation_id"):
                attestation_ids.add(evidence["attestation_id"])
            timestamp(evidence.get("issued_at"), f"{prefix}.evidence.issued_at", errors)
    if entries:
        first = entries[0]
        if first.get("sequence") != schema["sequence_must_start_at"]:
            errors.append("sequence_start_mismatch")
    if schema.get("sequence_must_be_contiguous") and len(entries) != len({e.get("sequence") for e in entries if isinstance(e, dict)}):
        errors.append("sequence_not_unique")
    evidence_index = {e.get("entry_id"): e for e in entries if isinstance(e, dict)}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("evidence"), dict):
            continue
        refs = entry["evidence"].get("evidence_ids", [])
        if refs and any(ref not in evidence_index for ref in refs):
            errors.append(f"unknown_evidence_reference:{entry.get('entry_id')}")
        att_id = entry["evidence"].get("attestation_id")
        if att_id and att_id not in attestation_ids:
            errors.append(f"unknown_attestation_reference:{entry.get('entry_id')}")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", default="current/PROVENANCE_EVIDENCE_CONTRACT.json")
    parser.add_argument("--ledger", default="current/PROVENANCE_EVIDENCE_LEDGER_FIXTURE.json")
    args = parser.parse_args()
    contract_path, ledger_path = Path(args.contract), Path(args.ledger)
    if not contract_path.is_absolute(): contract_path = Path.cwd() / contract_path
    if not ledger_path.is_absolute(): ledger_path = Path.cwd() / ledger_path
    errors: list[str] = []
    contract, ledger = load_json(contract_path, errors), load_json(ledger_path, errors)
    if contract is not None and ledger is not None:
        errors.extend(validate(contract, ledger))
    report = {"status":"PASS" if not errors else "FAIL","contract":display_path(contract_path),"ledger":display_path(ledger_path),"entry_count":len(ledger.get("entries", [])) if isinstance(ledger, dict) else 0,"errors":errors}
    print(json.dumps(report, sort_keys=True))
    return 0 if not errors else 1

if __name__ == "__main__":
    sys.exit(main())
