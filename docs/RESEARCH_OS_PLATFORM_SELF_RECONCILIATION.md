# Research OS Platform Self-Reconciliation

## Purpose

The Platform owns a bounded reconciliation loop that can detect structural
drift and repair deterministic path/reference defects without requiring an AI
agent to rediscover the repository structure on every failure.

This is a Platform capability, not a Laravel-only capability and not a second
runtime or authorization system.

## Canonical flow

```
Root / Registry
      ↓
Structure Index
      ↓
Reference Resolution
      ↓
Failure Localization
      ↓
Blast Radius
      ↓
Repair Plan
      ↓
Sandbox + Snapshot
      ↓
Repair
      ↓
Recon Again
      ↓
Validation
      ↓
Evidence
      ↓
Unified Final Gate
```

## What the Platform may repair automatically

Only deterministic, uniquely resolvable references are eligible:

- a missing repository-local path with exactly one matching canonical target;
- a stale canonical reference whose target can be resolved uniquely;
- bounded text references where replacement is exact and minimal.

The Platform must not guess between multiple targets.

## What remains protected

Authorization policy, owner privilege, evidence integrity, audit integrity,
security boundaries and release-gate authority are protected. A reconciliation
finding in those areas becomes evidence for review rather than an automatic
mutation.

## AI relationship

AI receives the reconciliation context instead of guessing repository paths:

```
AI request
  → Recon context
  → canonical path / contract / dependency evidence
  → constrained write set
  → AI patch
  → post-patch Recon
```

AI is a reasoning participant, not the structural source of truth.

## Long-term extension points

The same contract can later consume richer symbol/call/dependency indexes while
preserving the current canonical registries. New intelligence must compose
existing authorities rather than create competing registries.

## Release rule

Self-reconciliation never approves or releases itself. Every repair produces
evidence and remains subject to the existing Unified Final Gate.
