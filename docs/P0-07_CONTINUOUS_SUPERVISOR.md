# P0-7 Continuous Supervisor

P0-7 defines the decision boundary for schedule/retry/recover/rebalance/rescan.

The supervisor is **not an execution engine**. It observes canonical identity plus existing execution state and emits a declarative decision for existing queue/AEOS adapters.

Safety rules:

- conflict → QUARANTINE and preserve evidence
- expired lease → RECOVER through existing lease rules
- stale verification → RESCAN before renewed trust
- failed/retry-wait → RETRY with a new canonical attempt
- ready + dependencies satisfied → SCHEDULE
- otherwise → NOOP

No new queue, scheduler, state machine, or worker is introduced.
