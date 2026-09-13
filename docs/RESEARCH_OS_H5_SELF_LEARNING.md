# Research OS H5 — Bounded Self-Learning Governance

## Purpose

H5 governs the existing Friend self-learning engine so that learning remains bounded, evidence-backed, owner-scoped, and reversible through the existing promotion/registry boundary.

## Flow

```text
Verified runtime observation
        ↓
H5 Learning Contract
        ↓
bounded proposal
        ↓
existing validator + evaluator
        ↓
existing promotion gate
        ↓
approved learned-skill registry
```

H5 does not allow a learned candidate to mutate Core Skills. A candidate becomes reusable only through the existing validation, evaluation, and promotion gate.

## Contract rules

- exact Owner identity is required;
- exact source commit SHA is required;
- a bounded learning correlation ID is required;
- procedure length is bounded by the existing engine;
- evidence must be present before promotion is requested;
- malformed, secret-like, executable, or authority-like learning content is rejected;
- learned-skill snapshots are defensive copies;
- Core Skills are immutable from this contract;
- promotion remains governed by the existing `SkillPromotionGate`;
- the contract never grants merge, release, install, workflow-dispatch, shell, MCP, or Computer Use authority.

## Evidence rule

H5 accepts evidence as input but does not fabricate evidence. Real CI/runtime evidence must originate from the authoritative subsystem that observed it. The contract only validates and binds supplied evidence to the learning proposal.

## Bounds

- text fields: 2048 characters;
- procedure: existing six-step engine bound;
- evidence entries: 64;
- snapshot: 64 KiB;
- nesting: 6 levels.

## Failure behavior

Identity mismatch, missing evidence, unsafe content, unsupported values, excessive bounds, or malformed runtime state fail closed. Low-confidence or invalid candidates are not promoted and remain non-reusable.

## Authority

H5 is a learning subsystem, not a release subsystem. It cannot approve itself, rewrite evidence, mutate Git refs, dispatch workflows, merge pull requests, install releases, or change the release authority model.
