# Platform Virtual Workspace

The Platform Virtual Workspace is a **logical map**, not a second physical project tree.

## What Platform is about

- **FOUNDATION** — boundary and architecture
- **INTEGRATION** — composition and dependency resolution
- **EVOLUTION** — controlled change, simulation, validation and rollback
- **FEDERATION** — repository, service and domain federation
- **RESOURCE** — quota, provider, budget and capacity governance
- **SECURITY** — identity, supply chain, isolation and recovery
- **RELEASE** — evidence-bound release and certification
- **OPERATIONS** — monitoring, reconciliation, recovery and successor handoff

Virtual paths such as `PLATFORM/INTEGRATION` are metadata only. They do not require matching directories.

## Operating rule

Before starting Platform work:

1. Find its `PLATFORM-*` record.
2. Read its purpose and virtual path.
3. Resolve FOUND / PARTIAL / GAP / UNKNOWN.
4. Follow source and dependency references.
5. If UNKNOWN, investigate before creating anything new.
6. Register new work before implementation.
7. Attach evidence after verification.

## Gap rule

`UNKNOWN -> INVESTIGATE -> FOUND/PARTIAL/GAP`

`GAP -> BUILD AFTER INVESTIGATION`

UNKNOWN is never silently converted into GAP or DONE.

## Authority

The registry is descriptive only. It does not approve, merge, grant permissions, change branch protection or rewrite history. Existing Core, Assurance, Provenance, Learning, Resource, V3 and release controls remain authoritative.

## Goal

A future question such as **"Platform มีงานอะไรค้าง?"** should be answerable from this registry without reconstructing the answer from historical PRs.
