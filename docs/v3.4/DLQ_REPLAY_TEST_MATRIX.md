# V3.4 — DLQ + Replay Test Matrix

| ID | Scenario | Expected result |
|---|---|---|
| DLQ-01 | Retryable failure below max attempts | Task returns to existing queue after retry delay |
| DLQ-02 | Retryable failure reaches max attempts | Exactly one durable DLQ record |
| DLQ-03 | Non-retryable failure | Direct transition to DLQ |
| DLQ-04 | Duplicate failure callback | No duplicate DLQ record |
| DLQ-05 | Process restart with DLQ entries | DLQ entries remain durable |
| REP-01 | Authorized replay | One replay request enters existing queue |
| REP-02 | Duplicate replay request | No second active execution |
| REP-03 | Concurrent replay requests | Atomic idempotency; one effective execution |
| REP-04 | Replay after task already succeeded | No duplicate execution |
| REP-05 | Replay after lease expiry | Existing Lease/Ownership layer controls acquisition |
| REP-06 | Unauthorized replay | Request rejected and audited |
| REP-07 | Replay survives process restart | Replay request remains durable |
| REP-08 | Replay audit | Actor, replay id, task id, timestamp recorded |
| E2E-01 | Worker crash during execution | Lease recovery makes task eligible again |
| E2E-02 | Runner restart | Queue/task state is recoverable |
| E2E-03 | Duplicate event delivery | Idempotency prevents duplicate execution |
| E2E-04 | DLQ -> replay -> Worker Pool | Task completes through normal execution path |
| E2E-05 | Concurrent replay + original delivery | Exactly-once effective outcome |

## Required assertions

Every test should assert both state and side effects. A green status alone is insufficient.

For duplicate scenarios, assert execution count, not only queue count.

For recovery scenarios, assert that ownership is reacquired through the existing lease mechanism rather than by a replay shortcut.
