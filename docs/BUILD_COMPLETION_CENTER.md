# Engineering Build Completion Center

This document defines the inventory behind the future Engineering/Build UI.
It tracks unfinished tools, functions, platform capabilities, GUI work, and
production validation gates without presenting planned work as completed.

## Current priority order

1. Queue + Event Bus
2. Stateless Runner
3. Distributed Job State + Lease
4. Retry / Timeout / Idempotency
5. Runner Observability
6. Production Load + Concurrency Gate
7. Engineering Build Center UI
8. AI Conversation Center UI
9. Evidence Explorer UI

## Status model

- `blocked`: cannot proceed until a dependency is complete.
- `in_progress`: implementation exists and is actively being completed.
- `planned`: defined contract exists but implementation has not started.
- `ready_for_validation`: implementation is present and needs validation.
- `completed`: backed by code and passing validation evidence.

## Product rule

The UI and AI Conversation layer must read this registry rather than infer
completion from filenames, TODO comments, or optimistic status labels.

Every completion claim should be backed by tests, workflow evidence, or a
reviewed artifact.
