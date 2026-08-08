# ADR-0001: Local-first Structured Runtime Memory

- Status: Accepted
- Date: 2026-08-08
- Scope: Research OS v1.0 P0 Memory Engine

## Context

Research OS already has curated project knowledge stored as Markdown artifacts and retrieved through `memory.py`. Chat, agents, and future file intelligence also need structured runtime memory with CRUD operations, session/project metadata, timelines, and user-controlled deletion.

Replacing the curated artifact layer would create migration risk and would blur the boundary between public project knowledge and private application state.

## Decision

Research OS will maintain two explicit memory layers during v1.0:

1. **Curated artifact memory** — repository-backed Markdown artifacts retrieved by `memory.py`.
2. **Structured runtime memory** — local application records managed by `memory_engine.py`.

Structured runtime memory is local-first and defaults to `~/.research_os/memory/records.json`. It is not committed to Git and is not synchronized to cloud services automatically.

Completed chat streams may create conversation memories only when memory capture is enabled. The user must be able to inspect, search, and delete these memories from the Flutter Memory Inspector.

Deterministic keyword ranking is the P0 retrieval mechanism. Semantic embeddings remain deferred until privacy, migration, and storage behavior are stable.

## Consequences

### Positive

- Existing artifact retrieval remains backward compatible.
- Private runtime state is separated from repository knowledge.
- Memory can be audited and deleted by the user.
- Chat, agents, and file intelligence gain one reusable runtime-memory contract.
- The implementation stays dependency-light for P0.

### Negative

- Two memory systems coexist temporarily.
- Cross-layer search requires later unification in Universal Search.
- JSON storage is not intended to be the final high-scale database.

## Guardrails

- Never commit runtime memory files.
- Never expose secrets through memory inspection/status APIs.
- No implicit cloud synchronization.
- Interrupted streams must not be treated as completed assistant memories.
- Migration to another database must preserve the `MemoryRecord` contract and user deletion semantics.

## Follow-up

File Intelligence and Universal Search may consume the structured runtime-memory API after the Memory Engine P0 gate is complete.
