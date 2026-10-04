# Production Observability Runbook

Status: Draft operational handoff
Baseline: `main` @ `a06f0b7`

## Components

- Outbox publisher: `v3/scripts/drain_outbox.py`
- Metrics exporter: `v3/scripts/export_runtime_metrics.py`
- Durable queue database: configured queue SQLite path
- Durable event database: configured event SQLite path

The publisher is one-shot and should be run by an external scheduler. It must not be replaced by an in-memory loop that owns workflow state.

## Scheduled outbox drain

Run with a bounded batch and a stable workflow/correlation identity:

```text
python v3/scripts/drain_outbox.py \
  --queue <queue.db> \
  --events <events.db> \
  --workflow-id <workflow-id> \
  --correlation-id <scheduler-run-id> \
  --max-events 100
```

Exit code `0` means the batch completed without per-event failures. Exit code `1` means at least one event remains pending and should be retried. The command is safe to rerun because event IDs and published markers are durable and idempotent.

Recommended scheduler behavior:

- run every 15-60 seconds depending on queue volume;
- use a bounded batch to prevent one run from monopolizing the worker;
- alert after repeated non-zero exits;
- keep queue and event databases on durable storage;
- do not delete pending outbox rows during cleanup.

## Metrics scrape

Export metrics from the event database:

```text
python v3/scripts/export_runtime_metrics.py \
  --events <events.db> \
  --workflow-id <workflow-id>
```

The output is dependency-free Prometheus text. It contains counts only, not event payloads, credentials or session data. Expose it through the deployment's approved metrics endpoint or sidecar; do not expose the SQLite file or secrets over HTTP.

## Recommended alerts

| Signal | Initial threshold | Response |
|---|---:|---|
| Pending outbox events | greater than 0 for 10 minutes | inspect scheduler, event store availability and disk |
| Publisher failures | 3 consecutive runs | inspect error output and retry safely |
| Failed delivery count | increasing for 5 minutes | inspect consumer and event-store health |
| Claimed delivery leases | stale beyond configured lease | reclaim/retry and inspect crashed consumer |
| Queue depth | sustained above worker capacity | increase bounded capacity or investigate slow handlers |
| Provider circuit open | any production occurrence | inspect provider readiness and fallback status |

Thresholds must be tuned using production traffic before being treated as an SLO.

## Incident safety

- Preserve queue and event databases before repair.
- Replay pending outbox rows before considering data loss.
- Never manually mark an event published unless the destination event is verified.
- Keep server-only secrets outside logs, metrics labels, client bundles and evidence artifacts.
- Record deployment SHA, scheduler run IDs and recovery actions in the release evidence.

## Open production prerequisites

- Configure durable paths and scheduler identity on the target host.
- Provide a metrics scrape endpoint or sidecar.
- Configure alert routing and ownership.
- Test event-store outage and recovery on the target platform.
- Attach exact-SHA deployment evidence and runbook approval to release certification.
