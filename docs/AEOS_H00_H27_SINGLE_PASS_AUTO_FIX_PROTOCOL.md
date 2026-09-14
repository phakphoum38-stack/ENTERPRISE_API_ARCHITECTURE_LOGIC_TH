# AEOS H00-H27 Single-Pass Auto-Fix Protocol

## Status

**Proposed implementation contract** — operates on one exact target SHA and one consolidated repair lineage. It does not grant autonomous merge or constitutional authority.

## Objective

Inspect the complete H00-H27 horizon in one execution, collect every failure and missing control into one deterministic gap set, collapse symptoms to root causes, apply only bounded repairs through the existing Autobot repair boundary, and repeat verification until the target reaches `FINISHED` or a hard stop is proven.

The desired operating rule is:

```text
DISCOVER ALL
  -> CLASSIFY ALL
  -> COLLECT ALL FAILURES
  -> COLLAPSE TO ROOT CAUSES
  -> PLAN ONE REPAIR SET
  -> APPLY BOUNDED REPAIR
  -> RECHECK H00-H27
  -> repeat until FINISHED or HARD_STOP
```

## 1. Scope lock

The protocol treats H00-H27 as one graph, not 28 independent tickets. A run is bound to:

- exact `source_sha`
- exact `target_sha`
- protocol version
- contract version
- policy version
- correlation ID
- iteration ID

Any identity drift invalidates the current evidence set and requires re-anchoring.

## 2. Full-horizon discovery

Every pass evaluates all dimensions of every H node, even when an earlier node fails. The first pass must not stop at the first error because the purpose is to produce one complete gap set.

Required dimensions:

1. existence / identity
2. ancestry / lineage
3. source implementation
4. contracts and schemas
5. dependency closure
6. semantic behavior
7. tests and regression
8. workflow / CI
9. evidence / artifact
10. provenance / freshness
11. security / authority boundary
12. runtime / integration
13. recovery / rollback path
14. H-to-H compatibility
15. duplicate / supersession state
16. final lifecycle composition

## 3. Failure normalization

Every failure is normalized to a machine-readable record:

```text
failure_id
horizon
layer
symptom
observed_object
source_sha
target_sha
producer
verifier
raw_evidence_ref
fingerprint
severity
confidence
```

`UNKNOWN` remains `UNKNOWN`; it is never converted to PASS by inference.

## 4. Root-cause collapse

The Autobot must distinguish:

```text
symptom != detector != introducer != root cause
```

Multiple failures may map to one root cause. One root cause receives one repair intent. The consolidated repair set must not contain redundant fixes for the same causal defect.

## 5. Repair firewall

Autobot may:

- inspect
- classify
- propose a bounded fix
- apply a bounded source fix when policy permits
- add or repair regression tests
- collect fresh evidence
- retry verification

Autobot may not:

- weaken a failing gate
- delete required evidence
- rewrite canonical history
- self-approve its own change
- change constitutional invariants to make the run pass
- grant itself authority
- merge merely because a repair passes its own tests
- fabricate CI, provenance, or forensic evidence

## 6. One consolidated repair set

A pass may produce many file changes, but they belong to one causal repair set and one PR lineage. Do not create one PR per H node.

The repair set must contain:

```text
root_causes[]
repair_intents[]
changed_files[]
regression_tests[]
expected_invariants[]
blast_radius
risk_level
repair_fingerprint
```

If a proposed repair is unrelated to the observed root-cause set, it is rejected from the run.

## 7. Loop semantics

The loop is bounded, deterministic, and fail-closed.

```text
PASS  -> continue to next stage
FAIL  -> diagnose -> repair -> reverify
STALE -> re-anchor -> reverify
UNKNOWN -> HOLD
HARD_STOP -> HOLD
```

A retry is not a blind rerun. Every retry must produce new evidence and must preserve the meaning of the original failure.

Recommended default limits:

- maximum repair iterations: 10
- maximum re-anchors per run: 2
- maximum CI retries per repair iteration: 2
- maximum unchanged-failure retries: 1
- maximum total runtime: 2 hours

If the same failure fingerprint survives a bounded repair attempt without a changed causal state, the run enters `HARD_STOP:REPAIR_NOT_EFFECTIVE` rather than looping forever.

## 8. State machine

```text
DISCOVER
  -> ANALYZE
  -> GAP_SET_READY
  -> ROOT_CAUSE_READY
  -> REPAIR_PLANNED
  -> REPAIRING
  -> VERIFYING
  -> FULL_RESCAN
       | PASS
       v
     FINISHED
       |
       | FAIL
       v
     ANALYZE

Any state may -> HARD_STOP when a constitutional, identity,
security, provenance, authority, dependency, or budget invariant fails.
```

## 9. Full re-scan after every repair

After a repair, do not run only the previously failing H. Re-run the complete H00-H27 graph. This catches regressions introduced in a later H by a fix made for an earlier H.

A repair is successful only if:

```text
new failure set < old failure set
OR
root cause is demonstrably eliminated
```

A green local test for one file is never sufficient for `FINISHED`.

## 10. Completion predicate

`FINISHED` requires all of the following:

```text
H00-H27 discovered                    PASS
identity / exact SHA                   PASS
ancestry / dependency closure          PASS
source / contract integrity            PASS
semantic / blast-radius checks         PASS
full regression                        PASS
exact-head CI                          PASS
evidence integrity                    PASS
provenance / freshness                 PASS
security / authority boundary          PASS
cross-H integration                   PASS
recovery proof                         PASS
final lifecycle composition            PASS
independent verification               PASS
final gate                             PASS
```

`READY_FOR_OWNER_AUTHORITY` is not equivalent to `FINISHED` and is not merge authorization.

## 11. Evidence ledger

Each iteration records:

```text
iteration_id
attempt
source_sha
target_sha
failure_fingerprints_before
root_causes
repair_fingerprint
changed_files
failure_fingerprints_after
verification_result
manifest_fingerprint
```

The ledger is append-only for the run. Previous evidence is preserved when a later attempt supersedes it.

## 12. Main SHA fence

At every mutation boundary:

```text
OBSERVE MAIN
  -> PLAN
  -> BIND
  -> REPAIR
  -> VERIFY SAME MAIN
```

If main changes, dependent evidence is stale. The Autobot must stop, re-anchor, and regenerate the affected evidence before continuing.

## 13. PR consolidation rule

The complete run produces at most one repair PR for the current causal batch. Additional PRs are allowed only when a hard dependency or governance boundary makes consolidation impossible; such a split must itself be evidenced.

The PR description must include:

- exact source/base SHA
- all discovered H00-H27 failures
- collapsed root causes
- changed files
- regression tests
- evidence manifest
- repair fingerprint
- verification result
- explicit authority boundary

## 14. Independent verification boundary

The repairer cannot be the sole verifier. The final verification stage must consume fresh evidence independently of the repair operation.

```text
AUTOBOT REPAIRER
      |
      v
FRESH EVIDENCE
      |
      v
INDEPENDENT VERIFIER
      |
      v
FINAL GATE
```

## 15. Hard stops

Immediately stop autonomous progression on:

- exact SHA mismatch
- main SHA drift not successfully re-anchored
- dependency cycle
- unknown root cause after bounded analysis
- provenance invalid or stale
- evidence conflict
- contract drift
- security boundary violation
- authority escalation
- constitutional-policy modification attempt
- repeated ineffective repair
- repair outside declared scope
- CI not bound to exact head
- post-merge health failure
- decision replay mismatch
- retry/runtime budget exhaustion

Hard-stop output is `HARD_STOP`, never `PASS`.

## 16. Merge boundary

This protocol automates engineering work, not final authority. Even when H00-H27 reaches `FINISHED`, the established governance sequence remains:

```text
FINISHED
 -> FORENSIC
 -> INDEPENDENT REVIEW
 -> PRE-AUTHORITY
 -> AUTHORITY PACKET
 -> OWNER AUTHORITY
 -> MERGE
 -> POST-MERGE VERIFY
 -> REBASELINE
```

No loop is permitted to bypass these gates.

## 17. Recovery rule

Every successful repair iteration retains a verified predecessor. If post-repair verification destabilizes the system, recovery returns to the last certified state and records the failed repair as forensic evidence.

## 18. Learning rule

Only forensic-verified failures may become regression knowledge. The learning system may strengthen detectors and tests but may not rewrite constitutional policy or merge authority.

## 19. Final operating principle

> **Fail means diagnose, consolidate, repair, and verify again — not skip, suppress, or weaken the gate.**

The loop ends only at:

```text
FINISHED
```

or

```text
HARD_STOP + PRESERVED EVIDENCE + EXPLICIT RECOVERY CONDITION
```
