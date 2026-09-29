# Observability, Metrics and Tracing Coverage

Baseline: `main` @ `a06f0b7`

## Coverage matrix

| Capability | Current owner | Evidence | Status |
|---|---|---|---|
| Structured runtime events | `v3/research_os_v3/runner.py`, runtime event bus | V3 runner and worker pool tests | verified |
| Correlation IDs | `tools/research_os_api/v2_observability.py` | observability tests | verified |
| Secret redaction | `v2_observability.redact()` | `test_v2_observability.py` | verified |
| Readiness snapshot | `readiness_snapshot()` | V2 server and observability tests | verified |
| Diagnostics bundle | `diagnostics_bundle()` / `write_diagnostics_bundle()` | observability tests | verified |
| Worker lifecycle telemetry | worker pool event sink | `test_worker_pool_observability.py` | verified |
| Queue/runner recovery evidence | lease/reclaim events and evidence script | worker recovery evidence tests | verified |
| Durable event delivery metrics | `DurableWorkflowEventStore.metrics()` exposes event count, delivery attempts and safe status counters | `test_durable_events.py` restart/replay flow | verified locally |
| Outbox worker result | `v3/scripts/drain_outbox.py` emits JSON publish/failure counts and event metrics | CLI smoke validation | verified locally |
| Metrics export format | `v3/scripts/export_runtime_metrics.py` emits dependency-free Prometheus text | `test_runtime_metrics.py`; CLI smoke validation | verified locally |
| Durable append-only workflow event log | Workflow Runtime contract | durable event store not wired | gap |
| Metrics backend/export | No production metrics exporter identified | no deployment evidence | gap |
| Distributed tracing backend | Correlation exists, trace propagation/export is absent | no deployment evidence | gap |
| Alerting/dashboard | Workflow evidence exists; operational alert policy absent | no production evidence | gap |

## Current event fields

Structured events include timestamp, event type, correlation ID, run/task IDs and redacted detail. Runtime runner events include claim, retry, failure, completion and idle states. Worker recovery evidence records lease identity, reclaim count, final status and stale-ack rejection.

## Required production work

1. Select a metrics backend/scrape target and define counters, gauges and latency histograms without coupling the V3 contract to a vendor.
2. Propagate correlation/trace IDs across API, workflow engine, queue, runner and event consumers.
3. Persist lifecycle events through the durable event store described in `docs/DURABLE_RUNTIME_GAP_ANALYSIS.md`.
4. Define dashboard panels and alert thresholds for queue depth, lease expiry, retry exhaustion, DLQ growth, worker saturation, API errors and provider circuit state.
5. Attach exact-SHA deployment evidence, scrape/alert configuration and a log/secret-redaction review to release certification.

## Release decision

Local structured observability is implemented and tested. Production promotion remains blocked until durable event storage, metrics export, distributed trace propagation and operational alert evidence are available.

Operational handoff guidance is documented in `docs/PRODUCTION_OBSERVABILITY_RUNBOOK.md`.

The local event-store slice is protected by `.github/workflows/v3-runtime-event-store-ci.yml`.
