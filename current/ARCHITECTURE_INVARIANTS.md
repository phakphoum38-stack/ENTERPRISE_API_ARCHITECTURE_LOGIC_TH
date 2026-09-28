# Research OS Architecture Invariants

Status: CANONICAL

This document defines architectural rules that must remain true across Friend Service, Research OS, generation, execution, and release flows.

## Core Authority Boundaries

- **INV-001 — Orchestrator authority:** `FriendOrchestrator` is the execution authority.
- **INV-002 — Policy authority:** `OwnerPolicy` is the authorization authority.
- **INV-003 — Approval authority:** `ApprovalGate` is the authority for explicit approval of side effects.
- **INV-004 — Read-only discovery:** Tool Search / catalog discovery must not execute tools or create side effects.
- **INV-005 — MCP safety boundary:** The MCP boundary must not bypass authorization or approval policy to perform mutations.

## State and Execution

- **INV-006 — Approval before side effect:** A side-effecting operation must not execute without the required approved state.
- **INV-007 — Durable state:** Approval state that is defined as durable must survive runtime restart according to its schema contract.
- **INV-008 — Replay safety:** Side-effect execution must have an identifiable execution/request correlation boundary so retries cannot silently duplicate an operation.
- **INV-009 — Trace correlation:** Requests, approvals, tools, and executions must remain correlatable without persisting secrets or hidden model reasoning.

## Generation and Validation

- **INV-010 — Generated artifacts:** Generated artifacts must be produced from their declared source/template and generator; generated output must not become an undocumented manual source of truth.
- **INV-011 — Deterministic generation:** Identical source, generator, and configuration inputs must produce equivalent generated output. The current gate enforces deterministic generation inputs/canonicalization; generated-output equivalence remains a follow-up regression gate until a concrete generator/output pair is wired to it.
- **INV-012 — Validation after generation:** Generated output must pass its applicable validator/audit before it is promoted downstream.
- **INV-013 — Evidence over assumption:** Documentation may guide validation, but workflow/commit/artifact evidence is authoritative for release decisions.

## Build and Release

- **INV-014 — Exact source identity:** A build/release gate must verify the exact commit SHA used for the checked-out/build source.
- **INV-015 — Artifact identity:** The produced artifact must be identifiable as the intended target/user build before packaging.
- **INV-016 — Installed provenance:** The installed artifact must retain verifiable provenance back to the expected release source.
- **INV-017 — User isolation:** Four users are four isolated EXE targets; an artifact for one user must never be silently substituted for another user's target.

## Recovery and Change Control

- **INV-018 — Branch-isolated repair:** Automated repair must operate on an isolated repair branch and must not mutate `main` directly.
- **INV-019 — Stacked dependency order:** Stacked PRs must merge in dependency order: `#250 → #251 → #252 → #253 → #254 → #255` unless the dependency graph is explicitly changed and revalidated.
- **INV-020 — Failure isolation:** Infrastructure/validator fixes should remain independently reviewable when they are not part of the feature boundary they protect.

## Platform Governance

- **INV-021 — One canonical registry per domain:** Governance may reference canonical registries, but must not create competing registries or authorities.
- **INV-022 — No hard-coded surface cardinality:** Cross-platform surface validation derives identity and cardinality from canonical sources.
- **INV-023 — Change impact is explicit:** Governed changes identify affected components, contracts, risk, blast radius, and required gates.
- **INV-024 — Evidence coverage is attributable:** Completeness requires implementation, test, contract, evidence, provenance, and applicable gate coverage.
- **INV-025 — Governance is non-authoritative:** Governance validators may fail closed and report evidence, but cannot execute, authorize, approve, merge, or release.

## Self-Reconciliation

- **INV-026 — Recon before repair:** Structural repair must resolve the target against canonical repository state before mutation.
- **INV-027 — Deterministic repair only:** Automatic repair requires exactly one safe target and a minimal bounded replacement.
- **INV-028 — Protected-core fail closed:** Authorization, owner privilege, evidence/audit integrity, security boundaries, and release authority cannot be auto-repaired.
- **INV-029 — Post-repair reconciliation:** Every applied repair must be reconciled and validated again before promotion.
- **INV-030 — Repair reversibility:** Automatic repair must be performed in an isolated repair context with snapshot/rollback evidence.

## Enforcement Principle

Each invariant should be enforced by the narrowest appropriate mechanism:

```text
Architecture invariant
        ↓
Contract / schema
        ↓
Unit or integration test
        ↓
Validator / audit
        ↓
CI gate
        ↓
Release / installed gate
```

A document alone is not considered proof that an invariant is enforced.
