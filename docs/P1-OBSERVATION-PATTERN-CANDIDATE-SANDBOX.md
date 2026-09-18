# Phase 1 — Observation to Sandbox Boundary

## Purpose

Implement the first bounded portion of the Phase 1 learning flow:

Observation → Pattern → Candidate → Sandbox

## Contract

- Observations are immutable data.
- Patterns carry a deterministic SHA-256 observation fingerprint.
- Candidates retain the observation fingerprint in metadata.
- Sandbox creation is deterministic and data-only.
- Sandbox creation does not execute a candidate.
- Evidence remains explicit and is not fabricated.
- The component does not mutate Core Skills.
- No scheduler, queue, worker, execution engine, authority path, merge path, or workflow dispatch is introduced.

## Verification

Tests cover deterministic observation fingerprints, candidate lineage binding, deterministic sandbox identity, and fail-closed malformed observations.
