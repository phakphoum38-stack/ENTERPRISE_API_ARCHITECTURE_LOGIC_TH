# Adaptive Hierarchical AI Software Factory

## Purpose

This architecture is designed for large software projects that may need many isolated AI engineering teams at the same time without eagerly starting every possible agent.

The governing rule is:

> One active version gets one complete AI Software Factory, while Master Orchestrators scale hierarchically according to real workload.

## Logical power profiles

| Profile | Maximum logical factories | Intended use |
|---|---:|---|
| `1^3` | 1 | single-version / focused work |
| `3^3` | 27 | medium multi-version program |
| `6^3` | 216 | large program / many parallel workstreams |
| `6^6` | 46,656 | very large logical capacity |

These are capacity profiles, not eager process counts. The runtime creates only the hierarchy nodes and factories required for active work.

## Architecture

```text
PROJECT OWNER
    |
    v
GLOBAL CONTROL PLANE
    |
    v
MASTER ORCHESTRATOR L0
    |
    +--> MASTER L1 ... MASTER Ln
              |
              +--> VERSION FACTORY V1
              +--> VERSION FACTORY V2
              +--> VERSION FACTORY Vn
                         |
                         +--> Frontend AI
                         +--> Backend AI
                         +--> Database AI
                         +--> API AI
                         +--> Test AI
                         +--> Security AI
                         +--> Docs AI
                         +--> Build AI
                         +--> Migration AI
                         |
                         +--> Verification / CI / Release
```

## Core components

### Global Control Plane

Owns workload configuration, hierarchy planning, version-to-factory assignment, conflict coordination, and evidence records.

### Adaptive Hierarchy Planner

Selects the smallest power profile that can satisfy the current number of active factories, then lazily creates only the required orchestrator tree paths.

### Version Factory

Each version receives a complete nine-role specialist team and an isolated runtime namespace/worktree. A factory cannot mutate paths outside its own isolated workspace through the control-plane write boundary.

### Conflict Coordinator

Provides write leases so two factories cannot knowingly mutate the same resolved target at the same time.

### Evidence Ledger

Records important control-plane actions such as factory registration and write lease acquisition/release. A durable backend can replace the in-memory ledger later without changing the architecture contract.

## Adaptive execution rule

Example: ten active versions do not create all 27 factories available under `3^3`. The planner selects `3^3` because its capacity is sufficient, but activates only ten factory leaves and the minimum orchestrator nodes needed to reach them.

This keeps the logical architecture large while keeping runtime cost proportional to actual work.

## Version isolation

Recommended Git mapping:

```text
Version v1 -> version/v1 -> Factory v1
Version v2 -> version/v2 -> Factory v2
Version v3 -> version/v3 -> Factory v3
```

Released versions remain immutable snapshots. New changes should occur in a new draft/version branch and factory.

## Verification path

```text
Intent
  -> Plan
  -> Assign Factory
  -> Acquire Write Lease
  -> Implement
  -> Build
  -> Test
  -> Analyze
  -> Fix / Retry
  -> Evidence
  -> Git / CI
  -> Release
```

## Current implementation

- `software_factory/factory.py` — version factory and nine specialist roles
- `software_factory/hierarchy.py` — power profiles and lazy hierarchy planner
- `software_factory/control_plane.py` — assignments, conflict guard, evidence ledger
- `tests/test_adaptive_software_factory.py` — core behavior and isolation tests
- `.github/workflows/adaptive-software-factory.yml` — compile and unit-test CI gate

## Next expansion layers

The architecture intentionally leaves provider execution and persistent state behind interfaces. Future iterations can add a provider router, queue/worker runtime, persistent evidence store, dependency graph service, distributed locks, cost/token budgets, health telemetry, retry policies, and automatic Factory lifecycle scaling without changing the central 1-version-to-1-factory rule.
