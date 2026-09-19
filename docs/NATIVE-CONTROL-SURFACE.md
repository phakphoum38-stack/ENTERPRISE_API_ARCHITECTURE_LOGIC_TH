# Native Research OS Universal Control Surface

The Universal Control Surface is the reusable interaction layer behind the canonical Native Control Center.

## Scope

It provides one bounded model for:

- command discovery and preparation
- semantic search across registered Research OS objects
- universal inspection
- bounded lineage / "Why?" traces
- four-plane system mapping
- deterministic command fingerprints

It does not replace the existing Control Center, Runtime, Memory, Assurance, Learning, or authority systems.

## Interaction model

```text
USER
  ↓
CONTROL CENTER
  ↓
UNIVERSAL CONTROL SURFACE
  ├── SEARCH
  ├── INSPECT
  ├── TRACE / WHY
  ├── SYSTEM MAP
  └── COMMAND PREPARE
           ↓
     EXISTING ADAPTER
           ↓
      HUMAN AUTHORITY
           ↓
        EXECUTION
```

Command preparation is not execution. Navigation and inspection are read-only. High-risk approval, authorization, release, and merge authority remain outside this surface.

## Universal Inspector

Every registered object can expose a consistent shape:

```text
Identity
Type
State
Owner
Version
Relations
Dependencies
Provenance
Evidence
Confidence
Risk
History
Recovery
Successor
```

UNKNOWN values remain UNKNOWN until an authoritative adapter provides evidence.

## System Map

The map reuses the existing four planes:

- CORE
- ASSURANCE
- PLATFORM
- EXPERIENCE

It is a view over existing objects, not a second architecture registry.

## Bounds

- 100 search results per request
- 256 relations per inspected object
- 256 evidence references per inspected object
- 32 trace levels
- no unbounded crawling
- no network or filesystem I/O in the kernel

## Safety

The surface cannot:

- grant authorization
- approve a release
- merge a pull request
- modify branch protection
- rewrite history
- create a second scheduler, queue, memory, runtime, or assurance system

This layer is intentionally compositional: the Native Control Center remains the canonical UI surface, while existing adapters remain authoritative for real execution.