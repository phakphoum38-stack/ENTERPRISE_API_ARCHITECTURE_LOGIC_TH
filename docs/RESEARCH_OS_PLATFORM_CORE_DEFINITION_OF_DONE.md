# Research OS Platform Core — Definition of Done

This is the finite completion boundary for the shared Research OS platform.

The platform core is complete only when the existing canonical contracts,
capability delegation, lifecycle evidence, cross-surface parity, Phase E
distribution, Unified Final Gate binding, and the 100-project readiness
contract are all verified on one exact source SHA.

## What is shared

Projects share the existing platform planes:

- Capability Registry
- Authorization / Owner boundary
- Workflow model
- Event / Queue model
- Stateless Runner model
- Evidence / Provenance
- AEOS recheck
- Unified Final Gate
- Release authority

A project is a context and boundary, not a copied runtime.

## 100-project proof

The readiness harness instantiates exactly 100 project descriptors against the
same shared capability, queue, evidence, and Final Gate namespaces. It verifies
unique identity and cross-project idempotency separation.

This is a scale/readiness proof, not a claim that 100 concurrent production
workloads have been benchmarked. Capacity numbers beyond this deterministic
architecture proof require workload-specific performance testing.

## Exit condition

After Phase E passes and this completion gate passes:

1. Platform Core is treated as complete.
2. New projects add domain capabilities/configuration rather than another core.
3. New core infrastructure is added only when a concrete invariant is missing
   and must be explicitly reconciled into the canonical contracts.

The Unified Final Gate remains the sole release authority.
