# Research OS H1 — Generator / Autobot Boundary

**Status:** IMPLEMENTATION DRAFT — verification required
**Canonical predecessor:** `927d0015aacba1a70cc4405e4462b43e0e49adc3` (H0 Identity Foundation)
**Branch:** `feat/h1-generator-autobot-boundary`

## Purpose

Define a bounded, observable engineering loop in which Generator creates governed artifacts and Autobot diagnoses and repairs permitted repository changes without acquiring approval or release authority.

## Contract

1. Generator identity and outputs are represented by a bounded generation manifest.
2. A generation manifest binds its input to an exact source SHA and records output hashes.
3. Autobot mutations require an explicit capability budget and are recorded in an append-only action ledger model.
4. Failure classes distinguish retryable operational failures from integrity, policy, identity, provenance, and unknown failures.
5. Only explicitly retryable failures may consume the retry budget.
6. Repair attempts are bounded; repeated identical failure fingerprints trip a circuit breaker.
7. Autobot cannot approve, merge, release, install as release authority, bypass a gate, rewrite evidence, or silently escalate capability.
8. Unknown, malformed, conflicting, stale, or authority-relevant unsafe states fail closed.
9. A repair creates a new commit SHA and therefore requires fresh H0 identity capture and downstream CI verification.
10. This module is policy/state logic only. It does not dispatch workflows, mutate refs, publish releases, or fabricate generated evidence.

## Intended loop

```text
CI FAILURE
   -> capture evidence
   -> classify failure
   -> trusted research / diagnosis
   -> bounded repair plan
   -> capability safety check
   -> minimal permitted mutation
   -> new commit SHA
   -> authoritative CI
   -> PASS / new FAILURE
```

CI remains proof. Release Authority remains the release decision maker. Mission Control remains read-only.

## Non-goals

- no self-approval;
- no release authority;
- no auto-merge;
- no workflow dispatch implementation;
- no credential storage;
- no generated evidence substitution;
- no unbounded autonomous loop.
