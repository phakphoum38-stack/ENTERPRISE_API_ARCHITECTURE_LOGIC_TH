# Adaptive Trust Architecture

**Status:** Proposed architectural constitution
**Tracking:** #346
**Baseline:** `fab39afc15739c3dc9952f6f21db46d26f54b683`
**Historical P0-05 evidence:** #344 remains canonical, immutable, and read-only

## 1. North Star

> **Open by Design, Exact by Contract, Fail-Closed by Risk, Proven by Evidence, Reproducible by Version, and Continuously Improved by Forensics.**

The architecture must remain extensible without allowing extension to weaken identity, authority, provenance, policy, evidence, or execution boundaries.

## 2. Core Invariant

Every extensible object may be added without modifying unrelated core logic. No new object, capability, authority, policy, evidence type, version, agent, plugin, workflow, exception, or artifact receives implicit trust or authority merely because it exists.

**Extensibility is open; trust is earned; consequential decisions are exact.**

## 3. Universal Separation of Concerns

The following concepts are distinct and must not be implicitly collapsed:

- Identity != Capability
- Capability != Authority
- Authority != Trust
- Evidence != Authorization
- Provenance != Approval
- Policy != Execution
- Exception != Authority escalation
- Version != Approval
- CI green != Root-cause closure

A component may prove one property without acquiring another.

## 4. Universal Lifecycle

All consequential objects and decisions should be traceable through:

`DECLARE -> IDENTIFY -> VALIDATE -> BIND -> VERIFY -> AUTHORIZE -> EXECUTE -> PROVE -> AUDIT -> LEARN`

Not every object requires every stage operationally, but skipping a stage must be explicit in its contract and must not create an implicit trust path.

## 5. Flexible Extension Model

### 5.1 Open extension

The system must support addition of:

- new agents
- new capabilities
- new policy types
- new evidence types
- new provenance formats
- new execution modes
- new workflow stages
- new artifacts
- new schema fields
- new contract versions
- new integrations

### 5.2 Exact boundary

An extension becomes usable only after it is:

1. declared;
2. identified;
3. schema-valid;
4. contract-bound;
5. provenance-bound where applicable;
6. policy-evaluable;
7. authorized for its requested scope;
8. covered by regression evidence.

### 5.3 No hidden extension

Unknown fields, states, plugins, capabilities, policies, or authorities must never silently inherit an existing meaning.

## 6. Unknown-State Doctrine

`UNKNOWN` is a first-class state.

```text
KNOWN + VALID       -> eligible for policy evaluation
KNOWN + INVALID     -> REJECT
UNKNOWN             -> policy-defined BLOCK / REVIEW / DEFER
MISSING             -> REJECT or BLOCK according to contract
```

`UNKNOWN` must never silently become `PASS`, `VERIFIED`, `AUTHORIZED`, or `TRUSTED`.

Availability and trust are separate concerns: the system may retain or quarantine unknown data while still refusing consequential authority.

## 7. Fail-Closed by Risk

Fail-closed applies to consequential decisions, not necessarily to every storage or observation path.

Low-risk unknown input may be retained for review. High-risk unknown, missing, stale, revoked, expired, conflicting, or tampered evidence must block the consequential action.

The decision contract must define which states are blocking.

## 8. Versioning and Compatibility

Every extensible contract must have an explicit version.

Changes must be classified as:

- backward-compatible
- forward-compatible
- breaking

Compatibility must be tested rather than inferred from a successful import or CI run.

A new version does not automatically authorize previously unauthorized behavior.

## 9. No Silent Coercion

The system must not transform invalid or ambiguous input into valid trust state through hidden defaults or normalization.

Forbidden patterns include:

```text
missing -> PASS
unknown -> VERIFIED
invalid -> normalized-to-valid
mismatch -> silently reconciled
missing authority -> inferred authority
```

If coercion is necessary for compatibility, it must be explicit, deterministic, contract-defined, and evidence-bearing.

## 10. Authority Model

Authority must be scoped by at least:

```text
WHO
WHAT
WHERE / SCOPE
WHEN / EXPIRY
WHY
POLICY
EVIDENCE
```

Capability discovery does not grant authority. Registration does not grant authority. Trust claims do not grant authority. Successful authentication does not by itself authorize an operation.

Delegation must be bounded, expirable, revocable, and non-escalating.

## 11. Exception Model

Exceptions are controlled deviations, not bypass channels.

An exception should carry:

- issuer
- reason
- scope
- duration / expiry
- affected contract or policy
- evidence
- approval where required
- revocation semantics

Invariant:

`Exception != Authority Escalation`

An exception cannot grant broader authority than its issuer possesses.

## 12. Evidence and Provenance

Evidence is first-class infrastructure.

Consequential decisions should carry or reference:

```text
input references
contract version
policy version
identity
authority proof
provenance
fingerprint
verification result
reason
timestamp
```

Provenance should travel with consequential objects through transformations:

`INPUT -> TRANSFORM -> POLICY -> EXECUTION -> OUTPUT`

Historical/canonical evidence must remain immutable. New systems consume canonical evidence rather than rewriting it.

## 13. Determinism and Reproducibility

Where a decision is declared deterministic, the same effective inputs must produce the same decision:

`contract + policy + evidence + versioned inputs -> decision`

If the decision differs, the changed determinant must be observable and attributable.

Fingerprints must be computed over the contract-defined canonical representation, not an accidental serialization.

## 14. Decision-Carrying Evidence

A consequential decision must be explainable without reconstructing hidden state.

Minimum conceptual form:

```text
Decision
  -> decision state
  -> contract version
  -> policy version
  -> evidence references
  -> provenance
  -> authority context
  -> fingerprint
  -> reason
```

A bare `PASS` is insufficient for an auditable boundary.

## 15. Policy-as-Code Rule

The executable policy layer must preserve:

`Contract = Implementation = Tests = Evidence`

A declared policy mode must have real semantics. A mode such as `SEQUENCE` must not be accepted merely because it is syntactically present; either implement its ordering/dependency semantics or remove it from the allowed contract surface.

The evaluator must not trust caller-supplied `VERIFIED` claims as proof when the architecture requires independent verification.

## 16. Agent and Capability Model

Agents are extensible but untrusted by default.

```text
Agent registration
      !=
Agent trust
      !=
Agent authority
```

Capabilities should be composable and versioned:

```text
namespace
operation
scope
constraints
risk
version
```

A new capability never implicitly grants authority.

## 17. Execution Boundary

Execution must consume an already validated and authorized intent.

The executor must not silently repair, reinterpret, or broaden an upstream authorization decision.

Runtime results must obey their request/result invariants. For example:

`result.status == request.status`

when the contract defines status consistency.

## 18. Failure Forensics

Failure handling is a lifecycle, not a one-line fix:

```text
DETECT
  -> PRESERVE EVIDENCE
  -> CLASSIFY
  -> ROOT-CAUSE FORENSICS
  -> SOURCE FIX
  -> REGRESSION
  -> VERIFY
  -> ARCHIVE EVIDENCE
  -> PREVENTIVE RULE
```

Detector != introducer != root cause.

CI green is evidence of a passing check, not proof that the original root cause has been eliminated unless the regression explicitly covers the causal path.

## 19. Failure-to-Knowledge Conversion

Every material recurring failure should produce a reusable engineering rule, validator, test, contract clause, or diagnostic artifact.

The goal is not only to repair the current defect but to reduce the probability of the same defect class recurring elsewhere.

## 20. Universal Boundary Invariants

Every trust boundary should answer:

```text
WHO are you?
WHAT can you do?
WHAT are you allowed to do?
WHY are you trusted?
WHO authorized you?
UNDER WHICH POLICY?
WHAT EVIDENCE proves it?
WHERE did the data come from?
WHEN does it expire?
WHAT changed?
WHY was the decision made?
```

If a boundary cannot answer these questions, its contract must explicitly document the limitation and risk.

## 21. Architecture Layers

```text
L5 GOVERNANCE
   Constitution / Human Approval / Audit / Closure

L4 TRUST
   Identity / Authority / Capability / Policy

L3 PROOF
   Evidence / Provenance / Fingerprint / Attestation

L2 EXECUTION
   Agent / Workflow / Runtime / Artifact

L1 FOUNDATION
   Schema / Version / Contract / Compatibility
```

The layers may evolve independently only where their contracts preserve the invariants above.

## 22. Required Adversarial Matrix

Validators and boundary tests should progressively cover:

- VALID
- MISSING
- UNKNOWN
- STALE
- REJECTED
- REVOKED
- EXPIRED
- INVALID
- SCOPE ESCALATION
- WILDCARD SCOPE
- CONFLICTING AUTHORITY
- MISSING AUTHORITY PROOF
- INVALID PROVENANCE
- TAMPERED POLICY
- TAMPERED EVIDENCE
- TAMPERED FINGERPRINT
- EXPIRED EXCEPTION
- UNAUTHORIZED EXCEPTION
- HIGH-RISK WITHOUT APPROVAL

Coverage must be expanded according to the actual contract surface; this list is the baseline adversarial vocabulary, not permission to weaken a stricter contract.

## 23. Change Governance

Every material architectural change should identify:

```text
WHAT changed
WHY it changed
WHICH contract changed
WHICH policy changed
WHICH authority boundary is affected
WHICH evidence proves correctness
WHICH regressions cover the change
WHETHER compatibility is preserved
```

Proof-carrying changes are preferred over undocumented implementation-only changes.

## 24. Canonical History Protection

Historical production baselines and canonical evidence are not mutable merely to make current checks convenient.

For this architecture:

- P0-05 #344 is consumed as canonical evidence.
- Historical evidence must remain immutable.
- New architecture is layered on top of canonical history.
- Any correction to historical interpretation must be additive and traceable, not destructive.

## 25. Implementation Strategy

Adopt progressively rather than rewriting the repository in one step:

1. Establish this architecture contract.
2. Map existing H21-H27 boundaries to the universal lifecycle.
3. Harden boundary validators where evidence is currently caller-trusted.
4. Align contract declarations, implementations, and tests.
5. Add adversarial regression coverage.
6. Propagate compatible fixes through stacked branches.
7. Verify provenance/evidence without modifying #344.
8. Re-run full gates.
9. Record root-cause and verification evidence.
10. Rebaseline only after the evidence chain is complete.

## 26. Non-Goals

This architecture does not:

- grant runtime authority;
- replace OwnerPolicy;
- replace ApprovalGate;
- authorize an agent merely because it is registered;
- permit bypasses for convenience;
- make every unknown state fatal to system availability;
- permit rewriting canonical historical evidence.

## 27. Acceptance Criteria

The architecture is considered implemented only when the applicable subsystem demonstrates:

- explicit extension points;
- exact contract validation;
- fail-closed consequential decisions;
- explicit unknown-state handling;
- version and compatibility semantics;
- authority non-escalation;
- evidence/provenance binding;
- deterministic behavior where promised;
- adversarial regression coverage;
- forensic traceability;
- no mutation of canonical P0-05 evidence;
- green CI plus causal regression evidence.

## 28. One-Line Rule

> **Add freely. Trust deliberately. Validate exactly. Authorize narrowly. Prove continuously. Preserve history. Learn from failure.**
