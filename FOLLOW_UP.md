# Research OS Follow Up

Last updated: 2026-08-08

## Goal

Research OS v1.0

## Locked P0 Sequence

1. Chat Core
2. Provider Platform
3. Memory Engine
4. File Intelligence
5. Universal Search
6. Workspace
7. Release Candidate

No P1/P2 feature should interrupt this order unless a P0 blocker requires it.

## Current Status

### Chat Core
Status: COMPLETE FOR P0

Completed:
- Chat 2.0 shell integration
- NDJSON streaming transport
- Stop generation UI flow
- Copy / Retry / Edit Prompt
- Provider / Timestamp / Memory badges
- Streaming fallback contract

### Provider Platform
Status: COMPLETE FOR P0

Completed:
- Gemini
- OpenAI-compatible
- Ollama-compatible local path
- Provider readiness
- Provider capability endpoint
- Native upstream streaming where supported
- Streaming metrics
- Secret-safe status responses

### Memory Engine
Status: IN PROGRESS

Completed:
- Structured `MemoryRecord`
- Local-first JSON store
- Atomic writes
- CRUD foundation
- Tag/project/session/provider metadata
- Keyword ranking foundation
- Timeline foundation
- Unit tests for CRUD/search/timeline
- Runtime Memory HTTP API
- Runtime Memory API integration test covering create/search/timeline/update/delete

In progress:
- Integration with Chat memory capture
- Memory Inspector UI
- Documentation + ADR

Next:
- Add automatic conversation-memory capture policy
- Connect Flutter to runtime-memory endpoints
- Build Memory Inspector UI
- Add Memory Engine architecture documentation and ADR

## Runtime Memory API

- `GET /v1/runtime-memory`
- `POST /v1/runtime-memory`
- `GET /v1/runtime-memory/search?q=...`
- `GET /v1/runtime-memory/timeline`
- `POST /v1/runtime-memory/{id}/update`
- `DELETE /v1/runtime-memory/{id}`

The existing `/v1/memory/search` endpoint remains the curated artifact-memory compatibility API.

## Risks

- Existing `memory.py` is used by curated artifact retrieval. Do not replace it abruptly.
- Structured runtime memory must remain local-first and must not expose private local context in repository data.
- Semantic embeddings are intentionally deferred until deterministic storage/search behavior is stable.

## Architecture Decision

`memory.py` remains the curated artifact retrieval compatibility layer.
`memory_engine.py` is the new structured runtime-memory core.
They coexist during the migration so existing Research OS memory behavior remains compatible.

## Definition of Done: Memory Engine

- [x] Domain model
- [x] Local store
- [x] CRUD
- [x] Search foundation
- [x] Timeline foundation
- [x] Unit tests
- [x] HTTP API
- [x] Integration tests
- [ ] Chat integration
- [ ] Memory UI / Inspector
- [ ] Documentation
- [ ] ADR

## Next Module

File Intelligence starts only after Memory Engine Definition of Done is complete.
