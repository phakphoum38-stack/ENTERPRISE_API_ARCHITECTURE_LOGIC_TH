# AEOS Autonomous Workloop — Implementation Plan

## Rule

Implement in certified increments. Never modify the active H3 verification candidate merely to add future automation capabilities.

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

## Phase C — Recovery

- checkpoints
- crash resume
- quarantine
- rollback certificates
- disaster recovery
- chaos tests
- emergency freeze
- human escalation packet

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

## Phase F — Proof / Completion

- certificate chain
- engineering state root
- mission completion proof
- certified idle proof
- final drain verification
- post-merge verification
- re-anchor proof

## Phase G — Scale

- multi-agent execution
- multi-repository orchestration
- federated evidence
- cross-project dependency graph
- global incident correlation
- architecture evolution engine
- predictive failure prevention

## Delivery rule

Each phase must ship through the normal engineering lifecycle:

```text
branch -> docs -> source -> tests -> diff -> CI -> forensic review -> evidence -> provenance -> authority audit -> final gate -> certification -> merge -> main verification
```

If a phase discovers a failure, stop forward progression for the affected dependency, preserve evidence, identify the root cause, fix the source, and re-run the complete affected verification chain.
