# Provenance, Evidence Ledger & Proof-Carrying Changes

Status: CANONICAL

P0-05 makes critical engineering changes independently traceable and tamper-evident. `current/PROVENANCE_EVIDENCE_CONTRACT.json` is the canonical machine-readable contract.

## Core invariant

> Provenance is an assertion, not a claim. A declared digest has no authority until independently derived and verified against the exact declared identity and context.

```text
Declared Identity → Canonical Object → Deterministic Derivation → Actual Digest
        │                                      │
        └──────────── exact identity ──────────┘
                         ↓
                    VERIFIED / REJECTED
```

A Git commit/blob SHA-1 is a Git object identity. It is never accepted as an artifact SHA-256. Digest length is only a format check; algorithm, subject identity, canonicalization, derivation, and exact value are authoritative.

## Chain

```text
Identity / Authority → Action → Evidence → Typed Hash Identities
                                      ↓
                           Append-only Hash Chain
                                      ↓
                         Independent Verification
                                      ↓
                              Merge / Release Gate
```

Each entry has a unique ID, contiguous sequence, UTC timestamp, actor, action, subject, typed input/output hash identities, evidence, previous-entry hash, and entry hash. Entry hashes use domain-separated SHA-256 over canonical JSON without `entry_hash`.

## Identity and derivation rules

- Every digest is a typed record: `algorithm`, `digest`, `subject`.
- SHA-256 artifact identities are independently derived from the exact canonical object.
- Git SHA-1 is reserved for Git commit/blob identities.
- No truncation, padding, algorithm inference, repair, or silent downgrade is permitted.
- Canonicalization is versioned (`canonical-json-v1`) and UTF-8 deterministic.
- Target commits may be bound explicitly; stale or mismatched evidence fails closed.
- Producer output is a claim; verifier output is the authoritative verification result.

## Trust model

```text
Producer → CLAIM
Verifier → VERIFIED / REJECTED
Gate     → RELEASE_ACCEPTED (when policy permits)
```

A producer cannot self-verify high-risk evidence. Verification results are context-bound and must not be treated as timeless assertions.

## Regression and conformance

Mandatory negative coverage includes Git SHA-1 substituted for artifact SHA-256, malformed/truncated digests, wrong algorithm, changed payload, chain break, sequence gap, duplicate IDs, unknown references, stale target commit, and caller-supplied derived fields. The conformance suite and threat model are maintained under `tools/provenance_conformance/` and `docs/PROVENANCE_THREAT_MODEL.md`.

## Producer / verifier

`tools/record_provenance_entry.py` appends an entry and derives sequence, previous-entry hash, and entry hash. Derived fields cannot be supplied by the caller.

`tools/validate_provenance_evidence.py` independently recomputes the chain and validates schema, identity, derivation, timestamps, lineage, references, and target binding.

Verification:

```text
python tools/validate_provenance_evidence.py
python -m unittest tools.test_validate_provenance_evidence -v
```

## Failure model

Unknown critical data, unsupported algorithms, identity confusion, stale evidence, tampering, broken lineage, malformed hashes, and verification indeterminacy fail closed. Errors are machine-readable and must not expose secrets.

## Future-proofing

Hash-chain extensions, replay sequence, Merkle roots, migration compatibility, property-based tests, mutation testing, and multi-implementation differential testing are explicitly compatible with this contract but are not required to weaken the P0-05 merge boundary.

## Handoff

The verified evidence contract and validator are the machine-checkable evidence inputs for **#323 Policy-as-Code, Gate Compiler & Fail-Closed Enforcement**.
