# Engineering Build Center

- Document ID: ANEF-012
- Version: v1.0.0-draft
- Status: draft
- Purpose: GUI/UX contract for tracking unfinished tools, functions, platform capabilities, GUI work, dependencies, blockers, validation evidence, and AI-assisted continuation.

## Source of truth

The UI MUST read `current/BUILD_COMPLETION_REGISTRY.yml`. It MUST NOT infer completion from filenames, TODO comments, optimistic labels, or code presence alone.

## Main views

1. Overview — completion by priority and type.
2. Tools — unfinished and completed tools.
3. Functions — business/system functions and test coverage.
4. Builds — active implementation work.
5. Dependencies — dependency graph and blockers.
6. Validation — acceptance criteria and evidence.

## Status model

- blocked
- in_progress
- planned
- ready_for_validation
- completed

## Required cards

Every item card shows:

- name
- type
- priority
- status
- completion_percent
- dependencies
- acceptance criteria
- validation evidence, when available

## AI Continue

AI Continue may propose an implementation plan from the registry, dependency graph, code contracts, tests, and evidence. It MUST show the plan before executing high-impact changes.

## Safety rules

- Never present incomplete work as production-ready.
- High-impact actions require explicit approval.
- Completion percentage must be evidence-backed.
- Blocked items must expose their blocking dependencies.

## UX flow

```text
Build Center
  -> select item
  -> inspect contract
  -> inspect dependencies
  -> inspect validation evidence
  -> Ask AI / Continue Build
  -> review proposed plan
  -> implement
  -> validate
  -> update registry
```

## Acceptance criteria

- A user can find every unfinished registry item.
- A user can identify the reason an item is blocked.
- A user can see the dependency chain before starting work.
- AI can consume the same registry context.
- The UI cannot mark an item completed without validation evidence.
