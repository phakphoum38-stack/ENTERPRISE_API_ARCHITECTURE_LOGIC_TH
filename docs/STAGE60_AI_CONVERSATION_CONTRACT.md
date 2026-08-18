# Stage 60 — AI Conversation Contract

## UI contract

The Research OS chat composer is intentionally minimal:

```text
┌─────────────────────────────────────┐
│ เขียนข้อความที่ต้องการ...           │
│                                     │
│                         [สนทนา AI]  │
└─────────────────────────────────────┘
```

- The text field accepts normal text and multiline input.
- The `สนทนา AI` button is the explicit AI action.
- Typing alone must never call the AI provider.
- While a request is running, the action is disabled and reports `กำลังสนทนา...`.

## Runtime contract

```text
Flutter Chat UI
  -> ResearchOSApiClient.answerWithMemory()
  -> Research OS API
  -> AI provider
  -> answer + memory context
  -> Flutter response renderer
  -> local conversation persistence
  -> optional cloud conversation sync
```

A green CI job is not sufficient. Stage 60 is PASS only when the live application can complete a real conversation.

## Required capabilities

- Send a user message.
- Receive an AI answer.
- Preserve recent conversation context.
- Persist conversation sessions locally.
- Restore a previous session after app restart.
- Optionally synchronize a session to cloud storage when configured.
- Render normal text and Markdown answers.
- Copy an AI answer.
- Show provider/API errors without pretending the request succeeded.
- Expose memory usage when the API returns memory hits.
- Run API, Flutter, and end-to-end conversation checks.

## Test gates

1. API health.
2. Direct AI generation.
3. AI answer-with-memory.
4. Flutter chat widget contract.
5. Conversation persistence/restore.
6. End-to-end chat service.
7. Application launch/runtime check.
8. Browser Use connector check when enabled.
9. Only after all gates pass, regenerate the final workflow.

## Browser Use rule

Browser Use Cloud is an integration capability, not a fake local implementation. The smoke workflow must distinguish:

- implementation missing,
- credentials missing,
- mock/local mode,
- real cloud mode,
- runtime failure.

No test may manufacture a missing module merely to make CI green.

## Logical worker capacity

The project may describe a logical capacity of `20^20` helpers. This is a scheduling/capacity model, **not** a request to create `20^20` physical processes. Execution remains bounded by a worker pool, queue, timeout, and backpressure.
