# P0-10 Continuous Assurance / Fleet-wide Assurance Boundary

## Purpose

P0-10 adds a bounded, deterministic assurance projection over the existing
P0-8 fleet and P0-9 distributed coordination metadata.

It answers:

> Can the supplied fleet state establish the current assurance invariants?

It does **not** answer:

> May the system execute, authorize, merge, or release?

Those remain owned by the existing execution and governance planes.

## Inputs

- P0-8 `ProjectFleet` and canonical project identity.
- P0-9 `ConcurrentProject` bounded concurrency.
- P0-9 `CoordinationClaim` epoch fencing.
- P0-7 `SupervisorDecision` action projection.

## Assurance rules

PASS requires:

1. observation coverage equals the fleet size;
2. project, mission, and canonical work identities are unique;
3. every observation matches the registered canonical identity;
4. active concurrency is within its declared project bound;
5. supplied coordination claims are current and active;
6. supervisor actions are from the existing action vocabulary;
7. every supplied decision belongs to an observed fleet identity;
8. no required assurance input is silently treated as PASS.

HOLD is returned when an active supervisor condition such as
`QUARANTINE`, `RETRY`, `RECOVER`, or `RESCAN` remains present.

Stale/inactive/incomplete coordination input fails closed with an error rather
than being converted into PASS.

## Non-responsibilities

P0-10 does not:

- create a scheduler;
- create a queue;
- create workers;
- create a state machine;
- execute or retry work;
- apply supervisor actions;
- grant authority;
- authorize a release;
- merge code;
- mutate Git;
- repair source automatically.

## Evidence

`FleetAssuranceSummary.assurance_fingerprint` is a deterministic SHA-256
projection of the supplied assurance observations, decision fingerprints,
status, and reasons. It is an assurance artifact, not independent proof of
subject truth and not an authority certificate.

## Lifecycle boundary

Assurance is a read/projection boundary:

`observe -> validate -> summarize -> HOLD/PASS`

It must not become a second governance state machine. A PASS can support
existing verification/review flows; it cannot bypass them.
