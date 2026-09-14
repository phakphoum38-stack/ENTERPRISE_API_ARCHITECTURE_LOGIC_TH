# AEOS Universal Failure-to-Finish Protocol

## Status

**Proposed implementation contract** — one guarded failure intake and one causal repair loop for H00-H27 plus CI, tests, contracts, artifacts, provenance, security, runtime, and authority surfaces. It does not grant autonomous merge or constitutional authority.

## Objective

Discover failures across the complete assurance surface in one run, normalize them into evidence-bound records, correlate duplicate symptoms, collapse them to root causes, apply one bounded causal repair batch, and repeat full verification until `FINISHED` or an explicit `HARD_STOP` is proven.

```text
DISCOVER ALL
  -> INGEST ALL FAILURES
  -> NORMALIZE + IDENTITY/EVIDENCE CHECK
  -> CORRELATE / DEDUPLICATE
  -> ROOT-CAUSE GRAPH
  -> ONE CONSOLIDATED REPAIR SET
  -> REPAIR FIREWALL
  -> ONE REPAIR PR LINEAGE
  -> FULL REVALIDATION
  -> RE-INGEST FAILURES
  -> repeat until FINISHED or HARD_STOP
```

## 1. Universal scope lock

H00-H27 remains the core assurance horizon, but failures are not limited to H-node labels. Accepted scopes include `H00..H27`, `CI`, `TEST`, `CONTRACT`, `ARTIFACT`, `PROVENANCE`, `SECURITY`, `RUNTIME`, `RECOVERY`, `LINEAGE`, and `AUTHORITY`.

Every record is bound to an exact lowercase 40-character `source_sha` and traceable `evidence_ref`. Stale identity is a hard stop.

## 2. Universal failure record

Each non-PASS finding is normalized to:

```text
failure_id
scope
dimension
status
symptom
evidence_ref
source_sha
root_cause
severity
blocking
repair_required
verification_required
fingerprint
```

Evidence is mandatory. `UNKNOWN` root cause remains `UNKNOWN`; it is never inferred into PASS.

## 3. Discover all before repairing

The first pass collects the complete known failure set instead of repairing the first error and hiding downstream failures. H00-H27 dimensions include identity, ancestry, source, contracts, dependencies, semantics, tests, CI, evidence, provenance, security, runtime, recovery, cross-horizon compatibility, duplicate/supersession, and final lifecycle. External assurance scopes are ingested into the same ledger.

## 4. Correlation and root-cause collapse

```text
symptom != detector != introducer != root cause
```

Multiple failures across different scopes may represent one causal defect. They receive one root-cause key and one repair intent. Redundant fixes are rejected.

## 5. One consolidated repair batch

The default unit of repair is **one causal batch / one PR lineage**, not one PR per H node or per failing workflow. A batch contains:

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

Unrelated work is excluded rather than silently bundled. A split is permitted only when a hard dependency or governance boundary proves consolidation impossible.

## 6. Repair firewall

Autobot may inspect, classify, correlate, plan, apply bounded source fixes through an explicit adapter, add regression tests, collect fresh evidence, and reverify.

Autobot may never weaken gates, delete evidence, rewrite canonical history, self-approve, escalate authority, modify constitutional policy to pass, fabricate evidence, change branch protection, or merge as part of the repair stage.

## 7. Bounded fail-to-finish loop

```text
FAIL
 -> DIAGNOSE
 -> ROOT CAUSE
 -> REPAIR
 -> VERIFY
 -> FULL RESCAN
 -> RE-INGEST
```

Every repair must return a new exact source identity and trigger a complete verification scan. The loop is bounded by iteration, retry, re-anchor, and runtime limits. An unchanged failure fingerprint beyond its retry budget produces `HARD_STOP:REPAIR_NOT_EFFECTIVE`.

## 8. Evidence ledger

Each iteration records source identity, failure fingerprints before/after, root causes, repair fingerprint, changed files, verification result, and manifest/evidence references. The run ledger is append-only. Superseded evidence is preserved.

## 9. Completion predicate

`FINISHED` requires:

```text
all discovered failures ingested
all non-PASS failures have traceable evidence
all non-PASS failures have known root causes
all blocking failures closed
all required dimensions PASS
exact SHA identity PASS
full regression PASS
exact-head CI PASS
evidence + provenance PASS
security + authority boundaries PASS
independent verification PASS
final gate PASS
```

`READY_FOR_OWNER_AUTHORITY` is not `FINISHED` and is not merge authorization.

## 10. Hard stops

Hard stop on identity mismatch, stale evidence, unknown root cause, evidence conflict, provenance invalidity, contract drift, dependency cycle, security violation, authority escalation, constitutional modification, ineffective repair, out-of-scope repair, exact-head CI failure, decision replay mismatch, budget exhaustion, or post-merge health failure.

Hard stop is terminal for the current run: `HARD_STOP + preserved evidence + explicit recovery condition`.

## 11. Independent verification

The repairer cannot be the sole verifier. Fresh post-repair evidence is consumed by an independent verification boundary before `FINISHED`.

## 12. Governance boundary

A successful engineering loop does not merge itself. The established sequence remains:

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

No autonomous repair path bypasses these gates.

## 13. Recovery and learning

Every successful repair retains a verified predecessor. A destabilizing repair returns to the last certified state and records the failed attempt as evidence. Only forensic-verified failures become regression knowledge. Learning may strengthen detectors and tests but may not alter constitutional policy or merge authority.

## 14. Final operating principle

> **Fail means diagnose, consolidate, repair, and verify again — never skip, suppress, or weaken the gate.**
