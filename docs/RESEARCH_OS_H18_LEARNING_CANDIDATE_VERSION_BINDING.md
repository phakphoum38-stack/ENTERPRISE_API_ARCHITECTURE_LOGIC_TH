# Research OS H18 — Learning Candidate Version Binding

## Purpose

H18 prevents a learning candidate from being evaluated against a different skill version or result lineage than the one that produced its eligibility decision.

## Contract

`H17 ELIGIBLE CANDIDATE → VERSION BINDING → H10 PROMOTION EVALUATION`

The candidate remains bound to:

- exact owner;
- exact source commit SHA;
- exact correlation ID;
- exact skill fingerprint;
- exact result fingerprint;
- explicit candidate version.

A version mismatch, missing version, malformed fingerprint, or changed source identity fails closed.

## Authority Boundary

H18 does not promote, approve, register, execute, release, install, merge, dispatch, mutate refs, or fabricate evidence.

H10 remains the promotion authority. H18 only verifies that the candidate is still attached to the exact versioned learning lineage that produced it.

## Safety

Candidate content is bounded and rejects credential, executable, dynamic, approval, release, merge, install, dispatch, bypass, and authority-bearing content.

## Determinism

Version-binding snapshots are detached and deterministically fingerprinted. No network calls or persistence mutations are performed.

## CI

CI is authoritative for H18 acceptance.
