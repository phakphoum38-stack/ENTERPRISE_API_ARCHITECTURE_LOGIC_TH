# Research OS H17 — Learning Candidate Eligibility Boundary

## Purpose

H17 defines the read-only boundary between a validated H16 learning lifecycle result and a candidate that may be evaluated by the existing H10 promotion authority.

## Contract

`H16 LEARNING STATE → CANDIDATE ELIGIBILITY → H10 PROMOTION EVALUATION`

A result is eligible only when:

- the lifecycle envelope is `research-os-learning-lifecycle/v1`;
- owner, source SHA, correlation ID, skill fingerprint, and result fingerprint match exactly;
- the executor result status is `SUCCEEDED`;
- the lifecycle learning state is `LEARNED`;
- the lifecycle envelope remains `read_only=true` and `authority=none`;
- the result payload is bounded and free of credential, executable, dynamic, or authority-bearing content.

`FAILED` and `BLOCKED` results never become learning candidates.

## Authority Boundary

H17 does not promote, approve, register, execute, release, install, merge, dispatch workflows, mutate refs, or fabricate evidence.

H10 remains the promotion authority. H17 only determines whether a validated lifecycle result is structurally eligible to be presented to H10.

## Safety

The boundary fails closed on malformed envelopes, identity mismatches, unsupported lifecycle states, secret-like values, executable descriptors, dynamic instructions, authority-like fields, and oversized payloads.

## Determinism

Candidate snapshots are detached and deterministically fingerprinted from canonical content. The boundary performs no network calls and has no persistence authority.

## CI

CI is authoritative for H17 acceptance. A green local or planned state is not evidence of acceptance.
