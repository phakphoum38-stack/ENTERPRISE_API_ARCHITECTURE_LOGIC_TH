# Proof-Carrying Engineering OS

**Status:** Proposed system-wide engineering governance contract
**Parent architecture:** `docs/ADAPTIVE_TRUST_ARCHITECTURE.md`
**Tracking:** #346 / PR #347
**Canonical P0-05 evidence:** #344 remains immutable and read-only

## 1. Purpose

The Proof-Carrying Engineering OS (PCEO) turns every material engineering change into a traceable, verifiable, risk-aware object. A merge is not the mechanism that makes a change safe; merge is the final publication of a change that has already satisfied its evidence contract.

Core rule:

> **A change must carry enough proof to explain why it may enter the canonical system state.**

This layer is intentionally additive. It does not grant runtime authority, replace OwnerPolicy or ApprovalGate, or rewrite historical evidence.

## 2. Certified Change Lifecycle

```text
INTENT
  -> CLASSIFY RISK
  -> PRESERVE BASELINE
  -> IDENTIFY CHANGE
  -> TRACE ROOT CAUSE
  -> IMPLEMENT FIX
  -> VALIDATE CONTRACT
  -> RUN REGRESSION
  -> ADVERSARIAL VERIFY
  -> VERIFY PROVENANCE
  -> VERIFY HISTORY
  -> FINAL ASSURANCE
  -> CERTIFIED MERGE
  -> NEW CANONICAL BASELINE
  -> CONTINUOUS MONITORING
  -> FORENSIC LEARNING
```

`MERGE` is permitted only after the applicable preceding states are certified.

## 3. Change Object

Every material change should be representable as a Change Certificate with, at minimum:

```text
change_id
intent
risk_class
base_revision
head_revision
root_cause_ref
affected_boundaries
contract_refs
policy_refs
identity_context
authority_context
test_refs
ci_refs
evidence_refs
provenance
fingerprint
compatibility_class
blast_radius
approval_refs
verification_refs
expiry
baseline_target
```

Fields may be extended, but an extension must not silently change the meaning of an existing field.

## 4. Risk-Adaptive Assurance

Risk determines the depth of assurance, not whether evidence is required.

```text
LOW
  -> standard contract + regression + CI

MEDIUM
  -> LOW + expanded boundary tests + compatibility review

HIGH
  -> MEDIUM + adversarial verification + independent verification

CRITICAL
  -> HIGH + explicit human approval + complete provenance + release/baseline review
```

Unknown risk must not be downgraded to LOW. If risk cannot be classified, the consequential path is HOLD/REVIEW according to policy.

## 5. Root-Cause Integrity

A change certificate must distinguish:

```text
DETECTOR
INTRODUCER
SYMPTOM
ROOT CAUSE
FIX
VERIFIER
```

A green check is not sufficient to claim root-cause closure. Causal closure requires a regression that exercises the causal boundary or an explicit justified verification method.

## 6. Branch and History Integrity

Before merge, the proposed branch must establish:

- correct base lineage;
- intended head revision;
- no unresolved merge conflict;
- no accidental unrelated changes;
- required ancestor fixes are present;
- stacked-branch contracts remain compatible;
- the evidence refers to the exact revision being merged.

A downstream branch must re-verify inherited fixes after rebasing or equivalent history reconstruction.

## 7. Contract / Implementation / Test Triangle

For every declared invariant:

```text
          CONTRACT
          /      \
         /        \
 IMPLEMENTATION == TESTS
```

A contract statement without executable enforcement is incomplete. A test that contradicts the contract requires correction of the test or contract with documented rationale.

## 8. Adversarial Assurance

The assurance engine should actively attempt to invalidate trust assumptions.

Baseline mutation classes:

```text
missing evidence
unknown evidence
stale evidence
expired authority
revoked authority
scope expansion
wildcard substitution
conflicting authority
missing approval
tampered evidence
tampered policy
tampered fingerprint
replayed decision
duplicate event
version mismatch
contract downgrade
expired exception
unauthorized exception
runtime/result mismatch
```

Expected outcomes must be contract-defined. Consequential trust failures default to BLOCK/HOLD rather than silent acceptance.

## 9. Evidence Independence

A component must not be able to manufacture the evidence that it subsequently uses as the sole basis for trusting itself when independent verification is required.

Preferred chain:

```text
Canonical Contract
      -> Evidence / Authority Proof
      -> Provenance Verification
      -> Bound Evidence
      -> Policy Evaluator
      -> Decision
```

Forbidden trust shortcut:

```text
Caller
  -> {"verified": true}
  -> PASS
```

Self-attestation may be evidence of a claim, but it is not automatically proof of the claim.

## 10. Decision-Carrying Evidence

A consequential decision must preserve enough context to reproduce and audit the decision:

```text
decision
contract_version
policy_version
input_fingerprint
evidence_refs
provenance_fingerprint
authority_context
risk_class
reason
verification_refs
decision_timestamp
expiry
```

A bare `PASS` is insufficient for an auditable trust boundary.

## 11. Deterministic Decision Contract

Where determinism is promised:

```text
same effective inputs
+ same contract version
+ same policy version
+ same evidence state
= same decision
```

Any difference must identify the changed determinant. Serialization choices must be contract-defined and canonical.

## 12. Exception Safety

Exceptions are bounded deviations:

```text
issuer
reason
scope
contract/policy
approval
proof
evidence
issued_at
expires_at
revocation
```

Invariant:

`exception authority <= issuer authority`

No exception may silently broaden scope, remove required approval, disable provenance, or convert UNKNOWN into VERIFIED.

Break-glass exceptions are always time-bounded and auditable.

## 13. Blast-Radius Assurance

Before merge, identify affected surfaces from the dependency/change graph:

```text
Change
 -> files
 -> modules
 -> contracts
 -> policies
 -> tests
 -> workflows
 -> agents
 -> artifacts
 -> release surfaces
```

If the actual blast radius is larger than the declared radius, the change returns to REVIEW.

## 14. Continuous Assurance After Merge

Certification does not end at merge.

```text
MERGE
  -> baseline
  -> monitor
  -> detect anomaly
  -> correlate change
  -> assess blast radius
  -> quarantine / rollback if policy requires
  -> preserve evidence
  -> forensic analysis
  -> preventive rule
```

Rollback is itself a governed change and must produce provenance.

## 15. Forensic Knowledge Conversion

Material failures should become reusable knowledge:

```text
failure
 -> root cause
 -> invariant
 -> regression test
 -> validator/policy rule
 -> forensic record
 -> future detector
```

The goal is to make recurrence increasingly difficult.

## 16. Certified Merge Gate

A merge may be certified only when all applicable gates are satisfied:

```text
[ ] root cause identified or explicitly not applicable
[ ] source change verified
[ ] contract alignment verified
[ ] regression coverage verified
[ ] adversarial coverage verified for risk
[ ] CI required checks PASS
[ ] provenance verified
[ ] evidence references resolve
[ ] evidence belongs to exact head revision
[ ] branch ancestry verified
[ ] no unresolved conflict
[ ] compatibility verified
[ ] authority boundary preserved
[ ] canonical history preserved
[ ] final assurance PASS
```

Any `FAIL`, `ERROR`, `UNKNOWN`, `MISSING`, `CONFLICT`, or `UNVERIFIED` state blocks certification unless the governing contract explicitly defines a safe non-blocking disposition.

## 17. Canonical Main Doctrine

`main` is treated as the canonical verified system state.

Therefore:

> **Do not merge to make a branch become correct. Make the branch correct, prove it, then merge.**

Every successful merge creates a new baseline that downstream work inherits.

## 18. Stacked Branch Doctrine

For a stack:

```text
H25 -> H26 -> H27
```

The required order is:

```text
H25 certified
   -> merge
H26 rebased/aligned to certified H25
   -> certify
   -> merge
H27 rebased/aligned to certified H26
   -> certify
   -> merge
```

A downstream branch must not rely on an ancestor that was merely expected to pass.

## 19. No Self-Certification Shortcut

The author may implement a fix and generate evidence, but the verification model should provide independent checks where risk warrants it.

At minimum, the final gate must verify that:

- the evidence matches the exact head SHA;
- the claimed tests actually ran against that revision;
- the claimed provenance is valid;
- the policy used for the decision is the declared version;
- the decision has not been replaced by caller-provided trust state.

## 20. Governance State Machine

```text
PROPOSED
   -> ANALYZING
   -> IMPLEMENTING
   -> VERIFYING
   -> CERTIFIED
   -> MERGED
   -> BASELINED
   -> MONITORED

Any stage may transition to:
   HOLD / REJECTED / REVOKED

CERTIFIED does not mean permanently trusted; policy may expire or revoke certification.
```

## 21. Minimum Machine-Enforceable Invariants

1. Exact head revision binding.
2. Exact contract-version binding.
3. Exact policy-version binding.
4. Evidence reference integrity.
5. Provenance integrity.
6. No authority escalation through exceptions.
7. Unknown does not become verified implicitly.
8. Required negative cases block as specified.
9. Determinism where declared.
10. Historical canonical evidence is immutable.
11. Merge requires certified preconditions.
12. A merged revision becomes the reference baseline for downstream changes.

## 22. Implementation Roadmap

### Phase A — Architecture

- establish Adaptive Trust Architecture;
- establish this PCEO contract;
- define Change Certificate vocabulary.

### Phase B — Machine Contracts

- encode merge preconditions;
- encode risk classes;
- encode evidence/head-SHA binding;
- encode contract/policy version binding.

### Phase C — Verification

- add adversarial tests;
- add provenance verification;
- add branch/history checks;
- add blast-radius checks.

### Phase D — Governance

- require certified merge evidence;
- record canonical baseline after merge;
- prevent unsafe downstream inheritance.

### Phase E — Continuous Assurance

- correlate post-merge anomalies to changes;
- preserve forensic evidence;
- convert recurring failures into preventive controls.

## 23. Non-Goals

This contract does not:

- grant runtime authority;
- replace OwnerPolicy or ApprovalGate;
- mutate canonical P0-05 evidence #344;
- declare a PR safe merely because GitHub reports CI green;
- make every unknown storage/observation event fatal;
- permit bypasses for convenience.

## 24. Final Rule

> **Fix the cause in the branch. Prove the branch. Certify the change. Merge only certified state. Turn every failure into a stronger future boundary.**
