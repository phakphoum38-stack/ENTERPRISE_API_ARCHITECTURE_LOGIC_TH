# Persistent Self-Learning — Friend V1

## Purpose

Turn verified repair/research outcomes into durable, inspectable learned-skill records without allowing learning to mutate the immutable Core Skills.

## Lifecycle

`candidate -> validated -> reusable`

A failed or unverified attempt remains evidence only. `reusable` is the only state eligible for automatic reuse.

## Record contract

Every learning record carries:

- owner scope
- stable `skill_id`
- trigger/failure pattern
- decision source
- tools used
- source commit
- source workflow run
- changed files
- validation result
- PR reference
- verification timestamp
- confidence
- evidence references
- monotonically increasing record version
- deterministic fingerprint

This follows the existing Generate Skill Memory contract in `current/GENERATE_SKILL_MEMORY.md`.

## Safety boundaries

1. Core Skills are immutable.
2. Learned Skills are versioned records, not source-code patches.
3. Automatic reuse requires `reusable` state and owner scope match.
4. Promotion to `reusable` requires a successful validation result.
5. Evidence references remain attached so the Brain can re-check provenance.
6. Credentials are never persisted in learning records.
7. Learning records are local owner data and must not be bundled into source-only release artifacts.

## Persistence

The first implementation uses atomic JSON persistence. The storage location is supplied by the host/runtime, allowing Windows ProgramData deployment without coupling the learning engine to a specific machine path.

## Next gates

- unit tests for lifecycle and scope isolation
- integration with Friend orchestration/evidence
- promotion UI/API with explicit capability authorization
- rollback/rejection semantics
- migration to a richer store only after the JSON contract is proven
