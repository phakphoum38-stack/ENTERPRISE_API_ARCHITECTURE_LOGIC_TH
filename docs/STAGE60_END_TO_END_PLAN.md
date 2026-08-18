# Stage 60 — End-to-End Build / Run / Repair / Generate Plan

## Objective

Prove the real Research OS conversation path before declaring Stage 60 complete:

`UI → AI Conversation → API → Provider → Memory/History → persistence → Browser Use connector (when enabled) → E2E → build → runtime`

A green workflow alone is not sufficient.

## Execution model: 20^20

`20^20` is logical scheduling capacity only. It MUST NOT create 20^20 physical workers.

Use:
- bounded worker pool
- queue
- backpressure
- per-task timeout
- fail-fast prerequisite gates
- deterministic evidence for every gate

## Phase 0 — Inventory

Collect, without inventing files:

- Flutter Chat UI and tests
- Research OS API/client
- AI generation and answer-with-memory paths
- conversation persistence/history
- cloud conversation sync
- Browser Use connector/config/tests
- `.md` contracts/specifications
- GitHub Actions workflows
- build/install/runtime scripts
- ports and service mappings (8787–8792 where applicable)

Classify every expected component as `PRESENT`, `MISSING`, `MISMATCH`, or `NOT_APPLICABLE`.

## Phase 1 — Preflight

Run static checks before build:

1. YAML/workflow parse
2. Python import/compile
3. Flutter dependency resolution and analysis
4. test discovery
5. endpoint/port contract checks
6. required configuration/secret presence checks without printing secrets
7. UI contract checks for `เขียนข้อความที่ต้องการ...` and `สนทนา AI`

If a prerequisite is missing, STOP before the expensive build.

## Phase 2 — Build

Only after preflight passes:

1. build the Research OS target
2. collect build artifacts
3. record commit SHA and toolchain versions
4. run artifact sanity checks

## Phase 3 — Runtime

Start only bounded real services. Verify:

- `/health`
- AI generation
- `answerWithMemory`
- conversation persistence
- history restore
- cloud sync when configured
- Browser Use mock/local path
- Browser Use cloud path only when explicitly enabled and credentials exist

## Phase 4 — User-path E2E

Exercise the actual contract:

1. open app
2. find text composer
3. enter a message
4. press `สนทนา AI`
5. verify request reaches backend
6. verify AI response returns
7. verify response is rendered
8. verify conversation is persisted
9. verify history can be restored
10. verify failure states are visible and truthful

## Phase 5 — Failure loop

If ANY gate fails:

`FAIL → capture evidence → classify root cause → write repair plan → patch → regenerate affected workflow/test → rerun only failed prerequisite gates → full rerun`

Never mask a missing implementation by deleting its test.

## Phase 6 — Generate

Only after implementation and runtime behavior are proven:

- generate/normalize Stage 60 workflow
- generate documentation from the verified contract
- ensure generated workflow references existing files/tests only
- ensure `.md` contract and implementation agree

## Phase 7 — Final acceptance

Stage 60 is PASS only when:

- preflight PASS
- build PASS
- runtime PASS
- AI conversation E2E PASS
- persistence/history PASS
- Browser Use gate PASS or explicitly NOT_APPLICABLE with evidence
- generated workflow PASS
- no known implementation/test-name mismatch remains

## Evidence rule

For each gate record:

`gate | command/action | result | evidence | repair(if any) | rerun result`

No inferred PASS.
