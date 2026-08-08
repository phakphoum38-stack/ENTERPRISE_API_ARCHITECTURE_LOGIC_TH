# Research OS Memory Engine

## Status

P0 module. Structured runtime memory is implemented as a local-first subsystem and coexists with the curated artifact retrieval layer in `tools/research_os_api/memory.py`.

## Goals

The Memory Engine gives Research OS an inspectable, user-controlled memory store for conversations and future project/file memories without forcing cloud synchronization.

Core principles:

- Local-first by default.
- User-visible and deletable memory.
- No secret values in repository data.
- No automatic Git commit or cloud synchronization.
- Deterministic search before semantic embeddings.
- Backward compatibility with curated Markdown artifact retrieval.

## Architecture

```text
Chat / Agent / File Engine
          |
          v
Runtime Memory HTTP API
          |
          v
MemoryEngine
          |
          +--> JsonMemoryStore
          |       |
          |       +--> ~/.research_os/memory/records.json
          |
          +--> deterministic search/ranking
          |
          +--> timeline

Curated Markdown artifacts remain separate:
research/artifacts -> memory.py -> artifact retrieval
```

## Domain model

`MemoryRecord` contains:

- `id`
- `type`
- `content`
- `title`
- `source`
- `created_at`
- `updated_at`
- `project_id`
- `session_id`
- `provider`
- `tags`
- `priority`
- `metadata`

Records are immutable values. Updates replace the stored record and advance `updated_at`.

## Storage

The default store is:

```text
~/.research_os/memory/records.json
```

It may be overridden using `RESEARCH_OS_MEMORY_STORE` or the parent data directory using `RESEARCH_OS_DATA_DIR`.

Writes use a temporary file followed by atomic replacement. This reduces the chance of leaving a partially written JSON document after interruption.

## Runtime API

### List records

`GET /v1/runtime-memory`

### Search

`GET /v1/runtime-memory/search?q=<query>`

Optional filters include `type`, `project_id`, `session_id`, and repeated `tag` values.

### Timeline

`GET /v1/runtime-memory/timeline`

Optional filters include `project_id`, `session_id`, and `limit`.

### Create

`POST /v1/runtime-memory`

### Update

`POST /v1/runtime-memory/{id}/update`

### Delete

`DELETE /v1/runtime-memory/{id}`

## Chat capture policy

Completed streaming responses may be captured into runtime memory when memory capture is enabled. The current UI Memory switch enables the default capture policy through the streaming API.

A completed exchange creates two records:

1. User conversation record.
2. Assistant conversation record.

Both records share the chat `session_id`, provider information, role metadata, and conversation tags.

Interrupted streams are not persisted as completed assistant memories by this policy.

Memory capture stays on the local machine. It does not commit records to Git and does not synchronize them to cloud conversation storage.

## Memory Inspector

The Flutter application exposes a Memory Inspector from the App Shell. It supports:

- Listing runtime memories.
- Keyword search.
- Inspecting source/provider/tags.
- Selecting text.
- Explicit deletion with confirmation.

The inspector exists so AI memory is not a hidden state that users cannot audit or remove.

## Search and ranking

P0 search is deterministic. Query tokens are matched against title, content, and tags. Ranking currently combines:

- matched token count,
- title matches,
- record priority.

Semantic embedding search is intentionally deferred until storage behavior, privacy boundaries, migration, and deterministic retrieval are stable.

## Privacy boundary

Runtime memory is application data, not repository knowledge.

Do not:

- commit `records.json`,
- put API keys or passwords in a memory record,
- treat private runtime memories as public project facts,
- automatically sync runtime memory without explicit product policy and user control.

## Compatibility

`memory.py` remains responsible for curated Markdown artifact retrieval. `memory_engine.py` is responsible for structured runtime memory. These layers coexist intentionally during v1.0.

## Test coverage

The module currently includes:

- unit tests for CRUD/search/timeline,
- runtime HTTP API integration tests,
- streaming chat auto-capture test,
- Flutter Memory Inspector widget test.

## Next integration

File Intelligence may write file-derived memories using the same runtime-memory contract after the Memory Engine P0 gate is closed.
