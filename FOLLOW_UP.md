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
Status: IMPLEMENTATION COMPLETE — CI VALIDATION PENDING

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
- Privacy-first completed-chat auto-capture policy
- Local-only conversation capture with session/provider/role metadata
- Memory Inspector Flutter UI
- Runtime Memory Flutter API client methods
- User-controlled Memory search and deletion
- Memory Inspector widget test
- Streaming auto-capture integration test
- `docs/MEMORY_ENGINE.md`
- `docs/ADR/ADR-0001-runtime-memory-local-first.md`

Validation pending:
- Run the Python Memory/Streaming tests in CI or a local checkout
- Run Flutter analyze/tests including `memory_inspector_test.dart`
- Confirm Windows packaged app can read/write the configured per-user memory location

## Runtime Memory API

- `GET /v1/runtime-memory`
- `POST /v1/runtime-memory`
- `GET /v1/runtime-memory/search?q=...`
- `GET /v1/runtime-memory/timeline`
- `POST /v1/runtime-memory/{id}/update`
- `DELETE /v1/runtime-memory/{id}`

The existing `/v1/memory/search` endpoint remains the curated artifact-memory compatibility API.

## Privacy Boundary

- Runtime memory is local application data, not repository knowledge.
- Runtime memory is not committed to Git automatically.
- Runtime memory is not synchronized to cloud services automatically.
- The Memory Inspector makes stored memory visible and explicitly deletable by the user.
- Memory capture can be disabled through the chat Memory policy.

## Risks

- Existing `memory.py` is used by curated artifact retrieval. Do not replace it abruptly.
- Structured runtime memory must remain local-first and must not expose private local context in repository data.
- Semantic embeddings are intentionally deferred until deterministic storage/search behavior is stable.
- Memory Engine cannot be marked CI-PASSED until the relevant test suites actually execute successfully.

## Architecture Decision

`memory.py` remains the curated artifact retrieval compatibility layer.
`memory_engine.py` is the structured runtime-memory core.
They coexist during v1.0 so existing Research OS memory behavior remains compatible.

## Definition of Done: Memory Engine

- [x] Domain model
- [x] Local store
- [x] CRUD
- [x] Search foundation
- [x] Timeline foundation
- [x] Unit tests added
- [x] HTTP API
- [x] Integration tests added
- [x] Chat integration
- [x] Memory UI / Inspector
- [x] Documentation
- [x] ADR
- [ ] CI/local validation passes

## Next Module

File Intelligence starts after Memory Engine validation passes. No P1/P2 feature should interrupt this gate.
