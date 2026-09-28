# Phase 1 — Sandbox to Test Boundary

## Purpose

Implement the second bounded portion of the Phase 1 learning flow:

Sandbox → Test

## Contract

- A sandbox is validated as data; candidate procedures are never executed.
- Tests are declarative checks over sandbox structure and lineage.
- Test identity is deterministic SHA-256.
- Missing or malformed observation lineage fails closed when required.
- Test results contain explicit checks and failures.
- Test results are not evidence and do not create confidence or promotion authority.
- The component does not mutate Core Skills.
- No scheduler, queue, worker, execution engine, authority path, merge path, or workflow dispatch is introduced.

## Verification

Tests cover successful sandbox validation, deterministic test identity, fail-closed lineage validation, and configurable declarative checks.
