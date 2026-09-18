# 10^10 Logical Project Federation

## Boundary

P1 adds a **logical federation capacity of 10^10 projects (10,000,000,000)**.
This is an addressing and correlation boundary, not an instruction to allocate
10 billion in-memory objects.

The bounded operational registry remains:

- `ProjectFleet.MAX_PROJECTS = 100`
- existing Scheduler
- existing AEOS durable work graph
- existing queues/workers
- existing verification/evidence
- existing governance/authority boundaries

## Deterministic addressing

`TenBillionFederationProjection` maps:

`namespace + project_id -> ordinal -> partition_id + slot`

The default projection uses 1,000,000 logical partitions, yielding 10,000
logical project slots per partition. Addressing uses SHA-256 and is therefore
deterministic without maintaining a global mutable registry.

## Correlation

A logical address can be correlated with the existing `CanonicalIdentity`.
Distributed claims are validated against the same identity and fencing epoch.

This module does **not**:

- create a scheduler
- create a queue
- create workers
- execute work
- grant authority
- authorize merge
- mutate CI
- replace ProjectFleet
- replace AEOS

The intended topology is:

`10^10 logical projects -> canonical identity -> deterministic partition ->
existing distributed coordination -> existing AEOS graph -> existing execution
plane -> existing verification/evidence -> existing governance`

## Safety invariant

The 10^10 number is a **logical namespace capacity**. It must not be implemented
by changing the bounded operational fleet from 100 to 10^10.
