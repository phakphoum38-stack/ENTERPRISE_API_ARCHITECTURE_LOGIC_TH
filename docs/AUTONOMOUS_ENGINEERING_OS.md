# Autonomous Engineering OS (AEOS)

## Status

**Architecture proposal / governance specification**

This document extends the Adaptive Trust Architecture and Proof-Carrying Engineering OS into a repository-scale autonomous engineering governance model.

The objective is not autonomous merging for its own sake. The objective is a continuously verified engineering system in which changes can be discovered, diagnosed, repaired, proven, merged, observed, recovered, and converted into durable system knowledge without weakening trust boundaries.

## 1. North Star

> A change may move the system forward only when its identity, authority, intent, impact, correctness, provenance, and recovery path are sufficiently proven for its risk class.

AEOS treats `main` as a **Canonical Verified State**, not merely as the latest Git ref.

## 2. Scope

AEOS governs:

- change discovery and queueing
- dependency and ancestry management
- root-cause forensics
- change planning and bounded repair
- contract and policy validation
- semantic and blast-radius analysis
- exact-SHA identity binding
- evidence and provenance
- independent verification
- CI and regression verification
- certified merge
- post-merge verification
- rollback and recovery
- continuous assurance and drift detection
- failure-to-knowledge promotion
- historical replay and audit

It does not grant an agent unrestricted repository authority.

## 3. Constitutional Invariants

1. Identity is not capability.
2. Capability is not authority.
3. Authority is not trust.
4. Self-attestation is not independent verification.
5. `UNKNOWN` is neither `VALID` nor `INVALID`.
6. Evidence is first-class infrastructure.
7. Provenance binds evidence to the exact object and execution context.
8. Main changes invalidate dependent stale evidence.
9. Merge is the result of proof, not the place where proof is manufactured.
10. An agent cannot weaken the rule used to approve its own change.
11. Exceptions cannot escalate authority.
12. Breaking changes require explicit compatibility treatment.
13. Every merge has a recoverable verified predecessor.
14. Post-merge failure stops autonomous progression.
15. Every material failure becomes a candidate for durable regression knowledge.

## 4. Five-System Model

```text
L5 CONSTITUTION
   Governance / Human Approval / Audit / Closure

L4 TRUST
   Identity / Authority / Capability / Policy

L3 PROOF
   Evidence / Provenance / Attestation / Fingerprint

L2 ENGINEERING
   Queue / Agent / Workflow / Build / Test / Merge

L1 STATE
   Git / Artifacts / Runtime / Baseline / Recovery Points
```

AEOS adds three cross-cutting planes:

```text
CAUSAL PLANE     Failure → Cause → Fix → Outcome
TEMPORAL PLANE   State@SHA → State@SHA → State@SHA
MEMORY PLANE     Evidence → Knowledge → Regression → Prevention
```

## 5. Autonomous Change Lifecycle

```text
DISCOVER
  ↓
SNAPSHOT
  ↓
CLASSIFY
  ↓
DEPENDENCY CHECK
  ↓
ANCESTRY CHECK
  ↓
ROOT-CAUSE / INTENT CHECK
  ↓
PLAN
  ↓
BLAST-RADIUS / RISK
  ↓
PATCH / BUILD
  ↓
CONTRACT CHECK
  ↓
EXACT-SHA BINDING
  ↓
REGRESSION
  ↓
EXACT-HEAD CI
  ↓
EVIDENCE
  ↓
PROVENANCE
  ↓
INDEPENDENT VERIFICATION
  ↓
FINAL GATE
  ↓
CHANGE CERTIFICATE
  ↓
MERGE
  ↓
POST-MERGE VERIFY
  ↓
CANONICAL MAIN
  ↓
REBUILD QUEUE
  ↓
LEARN
```

## 6. Auto Horizon

The initial autonomous operating horizon is explicitly bounded:

```text
H0 → H24     GUARDED AUTO
H25          WAITING / DEPENDENCY CONTROL
H26          RESERVED
H27          RESERVED
```

The horizon must not advance merely because a timer elapsed or a queue item exists. Advancement requires the preceding range to be certified and main to remain healthy.

## 7. Queue Governance

AEOS maintains a queue snapshot containing:

- PR number and branch
- base SHA and head SHA
- merge base
- dependency parents and descendants
- changed-file set
- risk class
- contract versions
- evidence state
- provenance state
- CI state
- certification state
- supersession/duplication state
- recovery point

Only one dependency-safe change is processed at a time unless an explicit parallelism policy proves independence.

## 8. Main SHA Fence

Every autonomous operation binds to an observed main SHA.

```text
observe main SHA
      ↓
process change
      ↓
main changed?
  ├─ yes → invalidate → stop → re-anchor
  └─ no  → continue
```

A new main SHA invalidates dependent ancestry and any evidence that was scoped to the old target state.

## 9. Dependency and Ancestry Intelligence

PR metadata is insufficient evidence of lineage. AEOS must compare actual commit ancestry and changed-file topology.

A branch is considered stale when its effective merge base is not the current certified target state and the difference is material to the change.

Re-anchoring is itself a proof-carrying change and requires fresh exact-head verification.

## 10. Semantic Diff

AEOS evaluates more than line counts. It classifies changes by semantic impact:

- API/schema behavior
- contract behavior
- authority/trust boundary
- security boundary
- evidence/provenance semantics
- workflow semantics
- persistence/history semantics
- compatibility
- runtime behavior

A small textual diff may still be high risk.

## 11. Blast Radius

Blast radius considers:

```text
changed files
→ imported modules
→ contracts
→ policies
→ authority boundaries
→ tests
→ workflows
→ downstream branches
→ runtime surfaces
```

Risk classification must not be reduced solely to lines changed.

## 12. Independent Verification

The component that proposes or applies a change must not be the sole authority that verifies its correctness.

```text
Builder / Repairer
       ↓
Independent Verifier
       ↓
Policy / Final Gate
       ↓
Certificate
```

## 13. Anti-Self-Attestation

Caller-supplied `VERIFIED` fields are claims, not proof.

The minimum trust chain is:

```text
Canonical Contract
→ Evidence / Authority Proof
→ Provenance Verification
→ Bound Evidence
→ Evaluator
→ Decision
```

No evaluator may convert an unverified caller claim directly into a trusted state.

## 14. Evidence TTL and Freshness

Evidence has scope and freshness. It must record at minimum:

- source SHA
- target SHA
- contract version
- policy version
- producer
- verifier
- timestamp
- validity scope
- fingerprint

If the bound object or governing contract changes, the evidence becomes stale unless explicitly proven reusable.

## 15. TOCTOU Protection

The SHA observed during validation must remain the SHA bound to execution and verification.

```text
CHECK → BIND → EXECUTE → VERIFY SAME IDENTITY
```

A mutation between these stages invalidates the proof.

## 16. Decision Replay

A certified decision must be replayable from its recorded inputs:

```text
input
+ source SHA
+ target SHA
+ contract
+ policy
+ evidence
+ environment
= decision
```

Replay divergence is a certification failure.

## 17. Counterfactual Evaluation

For material-risk changes, AEOS may evaluate:

- merge now
- delay
- reject
- rollback after merge
- alternative change order

Counterfactual analysis informs risk decisions but cannot override constitutional invariants.

## 18. Shadow and Canary Modes

Changes may be evaluated without mutating canonical state through shadow execution.

High-risk changes may use canary progression before broader activation.

Neither mode may be used to manufacture evidence for a different SHA or policy state.

## 19. Circuit Breakers

Autonomous execution stops on:

- ancestry divergence
- unexpected files
- provenance mismatch
- repeated CI failure
- contract drift
- authority escalation
- evidence conflict
- security boundary violation
- post-merge health failure
- decision replay mismatch
- dependency cycle

A circuit breaker is fail-closed and requires explicit recovery criteria.

## 20. Retry Budgets

Retries are bounded by operation and risk class.

Retrying must not change the meaning of a failure. A retry may collect fresh evidence; it may not weaken a gate.

## 21. Dependency Deadlock and Starvation

The queue must detect dependency cycles and avoid indefinite starvation. Aging may increase scheduling priority but can never override safety or authority gates.

## 22. Duplicate and Supersession Detection

Before processing a PR, AEOS checks whether the change is:

- already present in main
- already merged through another branch
- superseded
- duplicate
- obsolete due to a newer root-cause fix

Duplicates are not merged merely because their CI is green.

## 23. Transactional Merge Model

```text
PREPARE
  ↓
VERIFY
  ↓
COMMIT
  ↓
POST-COMMIT VERIFY
```

A merge is not considered certified until post-merge verification establishes the new canonical state.

## 24. Recovery Fabric

Every certified main state records a recovery point:

```text
Certified State N
     ↓
Change
     ↓
Certified State N+1
```

Rollback must itself carry identity, reason, authority, evidence, and post-rollback verification.

## 25. Change Certificate

Each certified merge produces a machine-readable certificate containing:

- change identity
- source and target SHAs
- merge base
- root cause / intent
- changed scope
- risk and blast radius
- contract and policy versions
- test manifest
- CI evidence
- provenance root
- independent verifier
- recovery point
- decision
- timestamps

## 26. Global Change Ledger

Material mutations are append-only ledger events. This includes code, configuration, contracts, policies, workflow behavior, evidence state, and authority changes.

Audit history must be tamper-evident and linked to exact object identities.

## 27. Causal Engineering Graph

AEOS records relationships such as:

```text
failure
→ detector
→ introducer
→ root cause
→ affected object
→ fix
→ regression
→ evidence
→ merge
→ outcome
```

This preserves the distinction between symptom, detector, introducer, and root cause.

## 28. Engineering Time Machine

Historical states are replayable by SHA and associated governance state. The system must be able to explain what was known and why a decision was reasonable at a particular point in history.

## 29. Engineering Memory

Failures become candidate knowledge only after forensic verification.

```text
Failure
→ Forensics
→ Root Cause
→ Candidate Knowledge
→ Verified Rule
→ Regression
→ Prevention
```

The learning path itself is governed and cannot silently rewrite constitutional policy.

## 30. Engineering Immune System

The long-term objective is a feedback loop:

```text
Detect
→ Contain
→ Diagnose
→ Recover
→ Learn
→ Defend
```

Repeated failure patterns should become earlier detectors or stronger regression rules, subject to verification.

## 31. Engineering Genome

A canonical state can be represented by a versioned genome of:

- architecture
- contracts
- dependencies
- policies
- tests
- provenance
- risk posture
- history
- learned knowledge

Genome comparison helps identify semantic evolution that is not obvious from a textual diff.

## 32. Autonomous Learning Firewall

Agents may propose:

- fixes
- tests
- heuristics
- candidate rules
- knowledge records

Agents may not autonomously redefine:

- constitutional invariants
- trust boundaries
- authority model
- evidence requirements
- final merge authority

Those require governance treatment.

## 33. Kill Switch

Supported operating modes:

```text
AUTO_FULL
AUTO_GUARDED
AUTO_REVIEW_ONLY
AUTO_OFF
```

The kill switch must stop autonomous progression without corrupting evidence or canonical state.

## 34. Post-Merge Drift Detection

After merge, AEOS continuously evaluates whether the canonical state has drifted from its certified contract, policy, dependency, or runtime assumptions.

Drift creates a new evidence event and may trigger a circuit breaker.

## 35. Auto Does Not Mean Unbounded

The autonomy boundary is explicit:

```text
AUTOMATE EXECUTION
NOT TRUST
AUTOMATE VERIFICATION WORK
NOT AUTHORITY ESCALATION
AUTOMATE RECOVERY
NOT HISTORY DELETION
AUTOMATE LEARNING
NOT CONSTITUTIONAL SELF-MODIFICATION
```

## 36. H0→H24 Operating Rule

For the initial drain:

1. Snapshot current main.
2. Identify the next dependency-safe H item.
3. Verify actual ancestry.
4. Re-anchor if required.
5. Inspect isolated diff.
6. Run exact-head CI.
7. Run regression and forensic gates.
8. Verify evidence and provenance.
9. Produce a change certificate.
10. Merge only when certified.
11. Re-fetch main.
12. Post-merge verify.
13. Invalidate stale downstream evidence.
14. Rebuild the queue.
15. Continue only if the new main is healthy.

## 37. Hard Stops

No autonomous merge when:

```text
ROOT CAUSE UNKNOWN
ANCESTRY UNKNOWN
PROVENANCE INVALID
EVIDENCE STALE
AUTHORITY UNKNOWN
CONTRACT DRIFT
BREAKING CHANGE UNRESOLVED
SECURITY RISK UNRESOLVED
CI NOT EXACT-HEAD
POST-MERGE HEALTH UNKNOWN
```

## 38. Definition of Certified Main

`main` is certified only when:

```text
Code Identity       ✓
Contract Integrity  ✓
Policy Integrity    ✓
Evidence Integrity  ✓
Provenance          ✓
Regression          ✓
CI                  ✓
History             ✓
Recovery Point      ✓
Post-Merge Health   ✓
```

## 39. Final Rule

> **Autonomy may accelerate engineering, but proof remains the authority.**

The system may move quickly only because every important state transition remains observable, bounded, reproducible, explainable, and recoverable.
