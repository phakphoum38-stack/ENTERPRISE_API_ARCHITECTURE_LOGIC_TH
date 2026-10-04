# Research OS V3 API Contract Draft

Status: Draft
Version: `v3.0.0-draft`
Baseline: `main` @ `a06f0b7`

This document defines the stable V3 service-facing boundary identified by the V3 architecture. It does not supersede V1/V2 transport contracts until client migration and exact-SHA release evidence are complete.

## Service endpoints

| Method | Path | Purpose | Owner | Success |
|---|---|---|---|---|
| GET | `/health` | Service and safe dependency readiness | V3 service | `200` JSON health payload |
| GET | `/v3/master` | Return one orchestration decision for a workload | Unified Master Orchestrator | `200` decision payload |
| GET | `/v3/providers` | Return safe provider registry/readiness metadata | Provider Registry | `200` provider metadata |
| GET | `/v3/user` | Return validated user/profile scope metadata | UserContext/DataLayout | `200` safe scope payload |

## Request context

User-scoped requests use:

- `X-Research-OS-User`
- `X-Research-OS-Profile`

Both values are validated path components. Empty values, `.`/`..`, slashes, backslashes and traversal sequences are rejected. These headers identify a scope only; they never carry provider credentials.

## Response invariants

- Provider status returns safe metadata only: provider name, readiness, circuit state and retry metadata.
- `/v3/master` returns decision metadata, scale profile, capacity and reason; it never returns provider credentials.
- `/v3/user` returns scope metadata only and never returns credentials or data belonging to another user/profile.
- Health, status, audit and evidence payloads must not contain API keys, bearer tokens, OAuth client secrets, sync keys or session secrets.
- Error responses are JSON and must identify a stable error code without exposing secret values or unnecessary filesystem details.

## Master decision contract

The decision is provider-neutral and must include the selected scale/profile and bounded workload information. Logical capacity is a ceiling; implementations allocate lazily and must not pre-spawn maximum capacity.

```json
{
  "scale": "3^3",
  "fanout": 3,
  "depth": 3,
  "capacity": 27,
  "demand": 1,
  "provider": "mock",
  "reason": "..."
}
```

## Provider contract

Provider adapters are selected by the registry and remain behind a strict interface. Readiness and resilience checks may report availability, retry count and circuit state. Credentials are read from server-side secret sources only.

## Workflow runtime relationship

V3 API requests may create or inspect orchestration work, but durable execution follows the provider-neutral workflow contract:

`Intent -> Plan -> Workflow Engine -> Queue -> Stateless Runner -> Result/Event`

The workflow engine owns state, dependency resolution, retry and cancellation semantics. Queue delivery is at-least-once and execution must be idempotent. Every state transition requires an auditable event, and artifacts are stored outside the runner lifecycle.

## Data and lifecycle rules

- New mutable application data is scoped under `users/<user-id>/profiles/<profile-id>/`.
- Legacy root directories remain compatibility-only and are never auto-assigned to a user.
- Service restart, upgrade and uninstall preserve user data unless an explicit purge is requested.
- User/profile isolation and path traversal rejection are mandatory release checks.

## Compatibility and promotion gates

Before promotion from draft:

- define complete request/response schemas and stable error codes;
- map every V1/V2 client to a V3 operation or documented compatibility path;
- add API-level tests for auth, isolation, malformed context and secret-safe responses;
- prove queue lease, heartbeat, retry, DLQ, event idempotency and restart durability;
- run exact-SHA Windows, installer, Flutter and deployment evidence gates;
- record an owner-approved migration and rollback decision.

A V3 contract promotion must not delete V1/V2 surfaces by implication. Retirement requires an explicit replacement, migration path, tests and release evidence.
