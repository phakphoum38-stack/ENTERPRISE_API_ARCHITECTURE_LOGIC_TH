# Research OS H21 — Learning Promotion Record

## Contract

H21 creates a deterministic, read-only record from an **H20 eligible** learning candidate.

```text
H20 PROMOTION ELIGIBILITY
        │
        ▼
H21 PROMOTION RECORD
        │
        ▼
H10 PROMOTION AUTHORITY
```

H21 records eligibility; it does **not** perform promotion.

## Required invariants

- H20 schema must be `research-os-learning-promotion-eligibility/v1`.
- H20 decision must be `ELIGIBLE_FOR_H10`.
- Promotion authority remains `H10`.
- H21 output is `read_only: true` with `authority: none`.
- Owner, source SHA, correlation ID, skill fingerprint, result fingerprint, candidate version, and H18 binding fingerprint must match H20 exactly.
- The H20 eligibility fingerprint must match exactly.
- Candidate content is bounded and scanned for unsafe execution, credential, release, merge, install, dispatch, and bypass terms.
- The resulting record has a deterministic SHA-256 `record_fingerprint`.

## Record state

A valid record is emitted as:

```text
READY_FOR_H10
```

This is a readiness record, not an approval or promotion result.

## Authority boundary

H21 cannot:

- promote a learning candidate,
- approve a candidate,
- execute a skill,
- release or install artifacts,
- merge pull requests,
- dispatch workflows,
- mutate refs,
- rewrite evidence.

H10 remains the sole promotion authority.

## Evidence

The Python test suite is the executable contract. CI is authoritative. This document is design context and is not itself evidence of a passing gate.
