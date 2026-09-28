# Master Plan #329–#339 Forensic Integration Map

Status: forensic mapping only. This document identifies existing repository evidence and likely integration gaps; it does not certify completion of any Master Plan item.

## Canonical integration rule

Existing implementations are authoritative where their contracts and evidence already cover the requested capability.

- COVERED: repository evidence materially implements the requested capability.
- PARTIAL: meaningful implementation exists, but the Master Plan acceptance/DoD is not fully demonstrated by the observed evidence.
- GAP: no authoritative implementation was located by this forensic pass.
- UNKNOWN: evidence was insufficient to classify safely.

No duplicate subsystem should be created when an existing implementation can be linked or extended.

## Map

| Master Plan | Existing evidence observed | Initial classification | Integration target |
|---|---|---|---|
| #329 Institutional Memory / Provenance | `docs/RESEARCH_OS_CONTINUITY_INSTITUTIONAL_MEMORY_ARCHITECTURE.md`; Universal Learning Root provides provenance-bearing knowledge, learning events, evidence, recovery and history concepts | PARTIAL | Bind institutional memory schemas/retrieval and successor packaging to the Universal Learning Root without duplicating memory storage |
| #330 Controlled Evolution / Self-Improvement | Universal Learning Root has correction, transfer, recovery and promotion boundaries; AEOS autonomous workloop documents checkpoints, quarantine, rollback and disaster recovery | PARTIAL | Add explicit proposal → experiment → simulation → independent verification → evidence → risk/change budget → approval → safe execution → rollback → outcome-learning contract |
| #331 Federation | Cross-system identity/provenance concepts exist in AEOS assurance material, but no authoritative Master Plan federation contract was located in this pass | GAP/UNKNOWN | Define repository registration, cross-repo identity/provenance, ownership, trust, evidence federation and coordinated rollback |
| #332 Resource Governance | Existing repository contains resource-control and provider-governance workstreams; AEOS universe includes scheduling, concurrency, cost, capacity and resource dimensions | PARTIAL | Connect existing resource-control contracts to federation/global governance; do not create a second scheduler |
| #333 Security / Supply Chain / Resilience | `current/AEOS_ASSURANCE_ONTOLOGY.json` includes supply-chain, quarantine, recovery and security dimensions; AEOS workloop includes quarantine/rollback/recovery | PARTIAL | Bind threat model, supply-chain trust, compromise attribution/recovery and security regression evidence into one contract |
| #334 Formal Assurance / Proof | `docs/PROOF_CARRYING_ENGINEERING_OS.md`, `current/PROOF_CARRYING_CHANGE_CONTRACT.json`, AEOS ontology/universe, V3 10^1000 assurance protocol and current assurance fabric | PARTIAL/COVERED foundation | Integrate invariant catalog, proof freshness/invalidation and proof-carrying release into the existing assurance fabric |
| #335 Decision Intelligence | Decision provenance, counterfactual, risk and decision-governance dimensions exist in AEOS global assurance material; autonomous OS documents counterfactual risk decisions | PARTIAL | Add explicit alternatives/trade-offs, prediction vs outcome, resource economics and decision-learning linkage to Universal Learning |
| #336 Friend / Successor Handoff | Friend UI/runtime, executor handoff boundaries, continuity/institutional-memory architecture and recovery state exist | PARTIAL | Produce one evidence-backed successor/handoff packet contract spanning truth, active work, authority, evidence, recovery and next step |
| #337 Autonomous Operations Readiness | AEOS Master Assurance, final-gate/readiness documents, proof-carrying and V3 runtime assurance already provide substantial final-gate infrastructure | PARTIAL | Compose existing gates into one machine-verifiable end-to-end certification contract; do not create another assurance engine |
| #338 Continuous Operations / Stewardship | Continuous assurance watchdog, recon reconciliation, workflow integrity, security observer and 100PROJECT assurance fabric exist | PARTIAL/COVERED foundation | Add operating contract for freshness, drift, agent rotation, disaster drills, compaction and successor onboarding |
| #339 Rebaseline / Closure | Existing rebaseline contracts/records and historical immutability principles exist in repository history/workstreams | PARTIAL | Bind final archive, known-good declaration, open-risk register, successor package and generation transition to verified exact-SHA evidence |

## Dependency chain

```
#329 Memory / Provenance
      ↓
#330 Controlled Evolution
      ↓
#331 Federation
      ↓
#332 Resource Governance
      ↓
#333 Security / Resilience
      ↓
#334 Formal Assurance
      ↓
#335 Decision Intelligence
      ↓
#336 Friend / Successor Handoff
      ↓
#337 Autonomous Operations Readiness
      ↓
#338 Continuous Operations
      ↓
#339 Rebaseline / Closure
```

## Universal Learning integration

#469 establishes the shared learning root. The intended relationship is composition, not replacement:

```
Universal Learning Root
  ├─ knowledge / understanding / self-model
  ├─ observation → pattern → candidate → sandbox → test
  ├─ evidence → confidence
  ├─ conflict / correction / transfer / recovery
  └─ provenance + authority boundaries
             │
             ▼
      Controlled Evolution #330
             │
             ├─ proposal
             ├─ experiment
             ├─ simulation
             ├─ independent verification
             ├─ evidence
             ├─ risk/change budget
             ├─ approval class
             ├─ safe execution
             ├─ rollback
             └─ outcome learning
```

## Gap-first implementation rule

For each item, the next implementation must begin with exact evidence mapping:

1. Identify existing contracts, code, tests and evidence.
2. Bind them to the Universal Learning Root where appropriate.
3. Identify only unmet acceptance/DoD elements.
4. Implement only those gaps.
5. Re-run exact-SHA assurance.
6. Preserve existing authority boundaries and historical lineage.

## Explicit non-goals

- No duplicate global scheduler.
- No second memory system.
- No second assurance engine.
- No autonomous merge authority.
- No silent constitutional/authority mutation.
- No 10^1000 materialization.
- No replacement of the existing V3 assurance architecture.

## Conclusion

The Master Plan is not an empty backlog. Multiple items already have substantial implementation foundations. The largest clearly identifiable integration gap from this pass is the explicit Controlled Evolution lifecycle in #330 and the federation contract in #331. The remaining items should be treated as integration/composition work until a deeper exact-file/contract review demonstrates a true missing component.

This map is forensic guidance, not a completion certificate.
