# Research OS Unified Final Gate

## Purpose

Phase 6 adds one explicit release-gate contract over the existing Research OS
surface. It does not create a second executor, queue, scheduler, authorization
system, navigation registry, or release authority.

## Canonical spine

Identity → Capability → Authorization → Navigation → Page/Feature → Workflow
→ Event/Queue → Stateless Runner → Evidence/Provenance → AEOS Recheck →
Final Gate → Release.

The implementation validates the source and contract anchors that already exist.
Runtime execution and external tools remain subject to the canonical platform
contract.

## Required invariants

- The target SHA is explicit and verified after checkout.
- The canonical platform contract and golden release contract must exist.
- The shared navigation registry remains the source of truth.
- The current registry contains exactly 15 destinations with indexes 0–14.
- Desktop and mobile surface parity remains covered by the existing parity test.
- Every registered destination must map to a real page slot through the existing
  shell contract.
- Deferred work remains explicitly deferred; it is never converted to PASS.
- An unresolved deferred item blocks release certification.
- The Final Gate is the release authority; it does not grant merge authority.
- Unknown, missing, stale, conflicting, or mismatched evidence remains fail-closed.

## What this gate does not do

It does not add Workflow, Evidence, Final Gate, or Owner to the sidebar before
their actual capability/page/backend contracts exist. It also does not replace
the existing Research OS Gate, release-spine gate, platform matrix, evidence
lineage, or reconciliation workflows. Those remain independent evidence
producers; this gate provides the unified decision surface.

## Phase 6 acceptance

A Phase 6 change is complete only when the unified workflow validates:

1. exact source identity,
2. canonical and golden contracts,
3. shared navigation/page mapping,
4. Flutter surface,
5. Python surface,
6. explicit deferred semantics,
7. a single final decision job.

A green decision means all required checks in this workflow passed. It does not
silently reinterpret skipped or deferred work as success.
