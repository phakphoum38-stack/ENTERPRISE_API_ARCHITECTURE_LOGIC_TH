# Research OS H11 — Learning Registry Integrity

## Purpose

H11 adds an integrity boundary around promoted learned skills. H10 decides whether a candidate is eligible for promotion; H11 records a bounded, immutable registry entry so later runtime consumers can distinguish a verified promotion from mutable or fabricated learning state.

## Contract

`CANDIDATE → H10 PROMOTION DECISION → REGISTRY ENTRY → INTEGRITY FINGERPRINT`

A registry entry binds:

- exact Owner identity;
- exact source commit SHA;
- bounded correlation ID;
- learned-skill name and goal;
- evidence fingerprint;
- promotion fingerprint;
- registry version.

## Invariants

- Entries are immutable after insertion.
- Registry ordering is deterministic.
- Duplicate fingerprints are idempotent; conflicting content is rejected.
- Core skills cannot enter the learned-skill registry.
- Secret-like, credential-like, executable, dynamic, approval, release, or authority content is rejected.
- Snapshots are detached from internal state.
- Registry size and field lengths are bounded.
- The registry has no execution, approval, release, install, workflow-dispatch, ref-mutation, or evidence-fabrication authority.

## Safety boundary

H11 is a state-integrity and projection layer only. It does not execute learned procedures, alter Core Skills, approve promotions, dispatch workflows, mutate Git refs, merge pull requests, release/install artifacts, or create evidence claiming that CI passed.

CI remains authoritative for repository and release verification.
