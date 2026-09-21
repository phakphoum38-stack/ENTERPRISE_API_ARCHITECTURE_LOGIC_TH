# Research OS — Root Closure Mesh

## Purpose

The Root Closure Mesh is the cross-cutting closure model for Research OS. It combines source identity, provenance, semantic impact, failure diagnosis, bounded repair, diff closure, verification, evidence, lineage, and authority into one observable closure graph.

It is a projection and governance model, not a second execution engine.

## Canonical flow

```text
AI / Agent
  ↓
Run → PR → Branch → Commit SHA → Blob
  ↓
Source / Symbol / Value
  ↓
Consumer / Contract / Blast Radius
  ↓
Failure
  ↓
ROOT vs CASCADE classification
  ↓
Repair Sandbox
  ↓
Patch → Semantic Diff
  ↓
Regression / Contract / CI
  ↓
Evidence + Provenance
  ↓
Negative Proof
  ↓
Closure Certificate
  ↓
Authority Boundary
  ↓
Release
```

## Root dimensions

The canonical closure projection tracks:

- SOURCE
- PROVENANCE
- CHANGE
- SEMANTIC
- CONSUMER
- FAILURE
- REPAIR
- DIFF
- REGRESSION
- GENERATED
- SUPERSEDED
- DELETED
- EVIDENCE
- VERIFICATION
- AUTHORITY

Each dimension is first-class and may be CLOSED, REPAIRED, VERIFIED, BLOCKED, or UNKNOWN.

UNKNOWN is not success. The UI must never manufacture a positive state from missing telemetry.

## Closure rule

A code repair is not a globally closed root until:

```text
CODE FIXED
+ DIFF CLOSED
+ EVIDENCE PROVEN
+ LINEAGE COMPLETE
```

Authority and release remain separate states. Observation never grants approval, authorization, merge, or release authority.

## Failure semantics

The system distinguishes:

```text
ROOT_FAILURE
CASCADE_FAILURE
ENVIRONMENT_FAILURE
DATA / EVIDENCE_FAILURE
UNKNOWN_FAILURE
```

A cascade failure must reference its root rather than appearing as an independent root defect unless independent evidence proves otherwise.

## Provenance semantics

The UI should report:

```text
INTRODUCED_BY
CHANGE_OWNER
ROOT_CAUSE_ASSOCIATION
```

These are evidence-backed associations. The system must not assign fault solely from the last editor of a file.

## Repair boundary

Repair follows:

```text
authoritative source
 → isolated repair workspace
 → bounded patch
 → semantic diff
 → independent verification
```

Repair cannot silently mutate canonical history, bypass required gates, or grant itself release authority.

## Negative proof

Before a root is closed, the closure process must check for:

- superseded implementations
- deleted implementations
- rewritten or force-pushed lineage
- generated artifacts without authoritative source
- source without expected generated artifact
- orphan consumers
- duplicate implementations
- stale evidence
- stale SHA bindings
- unresolved dependency descendants

Failure to establish the negative proof keeps the relevant state open or unknown.

## Flutter role

Flutter Control Center is the human-facing operating surface and orchestration projection.

It may:

- show the causal/lineage graph
- identify the affected object
- show the associated agent/run/PR/SHA when proven
- prepare a bounded repair
- navigate to source and evidence
- show repair and verification state
- show why a root remains open

It must not:

- invent source or evidence
- infer authority from telemetry
- merge or release outside the governed authority path
- replace CI or independent verification
- rewrite canonical history

## Long-term autonomous repair

When an external AI introduces a defect, the intended operating sequence is:

```text
detect
 → bind exact identity
 → trace lineage
 → diagnose
 → locate authoritative source
 → create repair candidate
 → verify
 → record evidence
 → close root when proven
```

The user-facing result should make the causal chain explicit:

```text
WHAT BROKE
WHO / WHICH AGENT INTRODUCED THE CHANGE
WHERE THE AUTHORITATIVE CODE LIVES
WHAT WAS REPAIRED
WHAT PROVED THE REPAIR
WHETHER ROOT IS CLOSED
WHETHER AUTHORITY IS STILL REQUIRED
```

## Relationship to AEOS

This document consolidates the Root Closure Mesh with the existing Autonomous Engineering OS, evidence/provenance, authority, recovery, semantic diff, and independent verification rules. It does not replace those contracts and does not authorize workflow execution, merge, or release.