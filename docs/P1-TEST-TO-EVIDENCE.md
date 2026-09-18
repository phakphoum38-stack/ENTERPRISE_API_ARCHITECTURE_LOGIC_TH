# Phase 1 — Test to Evidence Boundary

## Purpose

Implement the next bounded portion of the Phase 1 learning flow:

Test → Evidence

## Contract

- Evidence is derived only from an explicit TestResult.
- Evidence binds to the originating test and sandbox identities.
- TestResult content is hashed deterministically.
- Evidence identity is deterministic SHA-256.
- Failed tests remain explicit failed evidence; they are not converted into success.
- Malformed test identity fails closed.
- This boundary does not execute candidates or rerun tests.
- It does not calculate confidence or authorize promotion.
- It does not mutate Core Skills.
- No scheduler, queue, worker, execution engine, authority path, merge path, or workflow dispatch is introduced.

## Verification

Tests cover deterministic evidence derivation, test/sandbox lineage binding, malformed identity rejection, and preservation of failed-test state.
