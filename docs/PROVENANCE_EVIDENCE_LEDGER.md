# Provenance, Evidence Ledger & Proof-Carrying Changes

Status: CANONICAL

P0-05 makes critical engineering changes independently traceable and tamper-evident. `current/PROVENANCE_EVIDENCE_CONTRACT.json` is the canonical machine-readable contract.

## Chain

```text
Identity / Authority → Action → Evidence → Input/Output Hashes
                                      ↓
                           Append-only Hash Chain
                                      ↓
                         Attestation / Independent Verify
```

Each ledger entry has a unique ID, contiguous sequence, UTC timestamp, actor, action, subject, input/output SHA-256 hashes, evidence, previous-entry hash, and entry hash. The entry hash is computed as SHA-256 over canonical JSON of the entry without `entry_hash`.

The first entry has `previous_entry_hash = null`; every later entry must point exactly to the preceding entry hash. This provides a deterministic tamper-evident chain.

## Proof-carrying requirements

- A change carries its source commit and evidence/attestation references.
- Artifacts, releases, and installations must retain backward lineage as required by the contract.
- Attestation records identify the subject, attester, statement, supporting evidence IDs, and issue time.
- Unknown or missing evidence references fail closed.

P0-04 supplies identity and authority. P0-05 records the resulting evidence; it does not grant authority or replace human approval for high-risk actions.

## Producer / consumer

`tools/record_provenance_entry.py` appends an entry, derives sequence and previous-entry hash, and computes the entry hash. Derived fields cannot be supplied by the caller.

`tools/validate_provenance_evidence.py` independently recomputes the chain and validates sequence, hashes, timestamps, evidence types, lineage, and references.

Verification:

```text
python tools/validate_provenance_evidence.py
python -m unittest tools.test_validate_provenance_evidence -v
```

## Failure model

Tampering with an entry, breaking the previous-hash link, introducing a sequence gap, duplicating an entry ID, using an unknown evidence reference, or providing malformed hashes/timestamps fails closed with a structured JSON report.

## Handoff

The verified evidence contract and validator are the machine-checkable evidence inputs for **#323 Policy-as-Code, Gate Compiler & Fail-Closed Enforcement**.
