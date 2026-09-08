# v0.3.0-alpha Snapshot

Status: Alpha baseline
Date: 2026-08-18

## Scope

Durable Execution Foundation.

## Included

- Queue / Scheduler / Runner reference orchestration
- Runner registry and health lifecycle
- Graceful drain
- Assignment reservation and fencing semantics
- Durable persistence contract
- PostgreSQL durable assignment adapter

## Release gates remaining

- Live PostgreSQL integration tests
- Durable runner registry and lease renewal
- Production queue adapter
- Retry / attempt persistence
- Multi-process validation
- Load and chaos testing

This snapshot is a development baseline, not a production release.
