# AEOS Autonomous Workloop — Implementation Plan

## Rule

Implement in certified increments. Never modify the active H3 verification candidate merely to add future automation capabilities.

## Phase 0 — Assurance Universe

- composable assurance ontology
- assurance domains, dimensions, states, risks, actors, and verification modes
- deterministic assurance-case compiler
- bounded combinatorial expansion
- high-risk case selection
- explicit assurance blind spots and unobserved space
- meta-assurance requirements for verifier correctness, independence, replay, and mutation resistance

The ontology is a model of the assurance space, not a certificate. The compiler produces deterministic case identities; concrete scanners and independent verifiers must supply the actual observations and evidence.

## Phase A — Foundation

- Mission Contract
- durable Work Item schema
- Work Graph
- queue/recovery queue
- explicit state machine
- exact SHA fence
- lease/lock model
- change/resource budgets
- failure fingerprinting

## Phase B — Verification

- semantic diff
- contract drift
- documentation drift
- dependency impact
- blast-radius analysis
- independent verifier
- adversarial verifier
- counterfactual verification
- evidence freshness
- decision replay
- assurance-case execution selected from the ontology

## Phase C — Recovery

- checkpoints
- crash resume
- quarantine
- rollback certificates
- disaster recovery
- chaos tests
- emergency freeze
- human escalation packet
- recovery replay verification

## Phase D — Continuous Operation

- Supervisor
- priority rebalancer
- scope-creep firewall
- intent-drift detector
- duplicate work detector
- autonomous discovery
- technical-debt queue
- maintenance queue
- cross-work dependency re-planning
- long-horizon drift detection

## Phase E — Trust / Security

- truth hierarchy
- agent reputation
- progressive autonomy
- autonomy decay
- tool capability firewall
- model-change firewall
- secret/PII firewall
- prompt-injection boundary
- supply-chain verification
- verifier diversity and self-approval prevention

## Phase F — Proof / Completion

- certificate chain
- engineering state root
- mission completion proof
- certified idle proof
- final drain verification
- post-merge verification
- re-anchor proof
- certificate replay
- temporal consistency
- provenance continuity

## Phase G — Scale

- multi-agent execution
- multi-repository orchestration
- federated evidence
- cross-project dependency graph
- global incident correlation
- architecture evolution engine
- predictive failure prevention
- global assurance coverage

## Delivery rule

Each phase must ship through the normal engineering lifecycle:

```text
branch -> docs -> source -> tests -> diff -> CI -> forensic review -> evidence -> provenance -> authority audit -> final gate -> certification -> merge -> main verification
```

If a phase discovers a failure, stop forward progression for the affected dependency, preserve evidence, identify the root cause, fix the source, and re-run the complete affected verification chain.

## Assurance rule

```text
Possible assurance space
        -> risk/coverage selection
        -> concrete observation
        -> independent verification
        -> evidence binding
        -> freshness / TOCTOU check
        -> final rescan
        -> certification
```

Never treat an unobserved case, caller-supplied projection, stale evidence, or self-attestation as a PASS.
