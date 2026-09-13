# Research OS H19 — Learning Candidate Integrity

## Purpose

H19 verifies that an H18 version-bound learning candidate remains internally consistent before any later promotion evaluation.

## Contract

`H18 VERSION-BOUND CANDIDATE → INTEGRITY VERIFICATION → H10 PROMOTION EVALUATION`

Integrity verification binds the exact owner, source commit SHA, correlation ID, skill fingerprint, result fingerprint, candidate version, and H18 binding fingerprint.

## Authority Boundary

H19 is read-only. It does not promote, approve, register, execute, release, install, merge, dispatch, mutate refs, or fabricate evidence.

H10 remains the promotion authority.

## Safety

Candidate payloads are bounded and reject credential, executable, dynamic, approval, release, merge, install, dispatch, bypass, and authority-bearing content.

## Determinism

The integrity snapshot is detached and deterministically fingerprinted. No network calls or persistence mutations are performed.

## CI

CI is authoritative for H19 acceptance.
