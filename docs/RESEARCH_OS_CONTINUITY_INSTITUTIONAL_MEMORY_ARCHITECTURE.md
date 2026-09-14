# Research OS Continuity & Institutional Memory Architecture

**Generation anchor:** `836229ed5337eca3a675ce1824e9386571a8bd01`
**Protected historical baseline:** `565ab068d5a1540ea799b594ff031ba003e068af`
**Status:** Canonical architecture specification for the continuity layer

## Mission

Research OS must preserve mission knowledge, verified truth, evidence lineage, operational context, authority boundaries, tooling knowledge, failure learning, and successor continuity outside any single chat, model, agent, or operator session.

The repository is the durable source of institutional memory. Chat/model memory is convenience context and is never the sole authority for verified truth.

## Non-negotiable invariants

1. Protected historical truth is immutable; never rewrite or erase verified history.
2. New generations extend or supersede prior generations with explicit lineage.
3. `KNOWN`, `OBSERVED`, `EVIDENCE_BOUND`, `VERIFIED`, `ASSURED`, and `CERTIFIED` are distinct states.
4. Documentation is not evidence merely because it declares a result.
5. Evidence without provenance is incomplete.
6. Authority cannot be granted or escalated by the agent that receives or exercises it.
7. A changed canonical SHA invalidates dependent work evidence until re-verification.
8. Conflicts, unknowns, stale evidence, and revocations fail closed.
9. Failure evidence is preserved before repair and promoted into reusable knowledge when material.
10. Agent/model/tool replacement requires context recovery and applicable re-verification.
11. Owner Authority remains human authority; automation may prepare and recommend but cannot impersonate Owner approval.
12. No continuity artifact may weaken existing AEOS, provenance, evidence, or protected-baseline controls.

## State model

```text
DECLARED
   ↓
OBSERVED
   ↓
EVIDENCE_BOUND
   ↓
VERIFIED
   ↓
ASSURED
   ↓
CERTIFIED
```

A transition must name its evidence and verifier. A lower state must never be silently interpreted as a higher state.

## Institutional memory domains

- Constitution and invariants
- Operating protocols
- Verified truths
- Architectural decisions and rationale
- Assumptions and unknowns
- Failures, root causes, fixes, and lessons
- Evidence and provenance
- Flight/operational recorder
- Tool and runtime trust metadata
- Agent/model drift
- Authority, leases, revocations, and audit
- Current mission and generation state
- Context recovery
- Successor handoff
- Certification and release state

## Context Recovery Protocol

A new agent/session MUST reconstruct context from repository state before making consequential changes:

1. identify repository and canonical branch;
2. identify canonical SHA and protected baseline;
3. load constitution and active invariants;
4. load current generation and mission state;
5. load verified truths and current evidence roots;
6. load open risks, assumptions, unknowns, and active failures;
7. load authority and capability boundaries;
8. load tooling/runtime registry;
9. load successor/handoff state;
10. determine the next permitted action from evidence, not conversation memory.

If required context is missing, contradictory, stale, revoked, or unverified, recovery is `FAIL_CLOSED`.

## Failure → Knowledge protocol

```text
Failure
  → immutable failure evidence
  → root-cause classification
  → source correction
  → regression test
  → provenance
  → forensic verification
  → lesson / knowledge record
  → prevention rule
```

A known historical failure must not be rediscovered merely because a new chat or agent was started.

## Tool trust protocol

Each consequential tool is represented by identity, version, purpose, authority boundary, invocation contract, evidence output, and known failure modes. Tool knowledge is descriptive and does not grant authority.

## Drift protocol

Changes to policy, constitution, model, agent, runtime, dependency, toolchain, schema, or evidence rules are drift events. Dependent certificates and evidence must be re-evaluated according to their declared scope.

## Revocation protocol

Evidence, authority, capabilities, certificates, and decisions may be revoked. Revocation must propagate to dependent artifacts and must not be hidden by stale cached state.

## Generation protocol

```text
Generation N
  → verified state
  → successor packet
  → context recovery
  → delta/reconciliation
  → re-verification
  → Generation N+1
```

Generation N remains immutable. Generation N+1 cannot inherit certification merely because it inherited files.

## Completion path

```text
Continuity Architecture
  → Institutional Memory
  → Context Recovery
  → Tool / Failure Knowledge
  → Mission Certification (#337)
  → Continuous Mission Assurance (#338)
  → Program Closure / Rebaseline (#339)
  → Next Verified Generation
```

## Forbidden shortcuts

- Treating chat history as canonical memory
- Copying a prior certificate without re-verification
- Declaring certification from a checklist alone
- Allowing an agent to approve its own authority
- Silently changing canonical SHA assumptions
- Rewriting protected baseline history
- Deleting failure evidence after repair
- Treating stale evidence as current
- Creating a parallel architecture instead of extending existing AEOS controls

## Change control

This document is an architecture contract. Changes must use the existing Research OS assurance chain:

`Failure Evidence → Root Cause → Source Change → Test → Provenance → Forensic → Independent Review → Pre-Authority → Owner Authority → Merge → Post-Merge Master Gate → Rebaseline`
