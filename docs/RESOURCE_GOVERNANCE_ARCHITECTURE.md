# Research OS Resource Governance & Entitlement Architecture

Status: Foundation implementation proposal

Baseline generation: `e22ae1115f14d4c562892d183fb4b980a5b828b7`

## Purpose

Create one provider-agnostic resource-governance layer for Research OS. API keys are an identity credential inside this architecture, not the owner of quota policy.

## Boundary

```text
Identity
  -> API Key / Session / Device
  -> Entitlement
  -> Policy
  -> Quota
  -> Reservation
  -> Scheduler / Router
  -> Execution
  -> Usage / Cost
  -> Evidence / Provenance
```

The governance layer may allow, deny, or throttle resource consumption. It does not own Research OS lifecycle, authority, certification, merge decisions, or generation transitions.

## Canonical concepts

- **Identity**: who or what is calling.
- **API Key**: a revocable credential bound to an identity and scopes.
- **Entitlement**: what the principal is allowed to use, including tier, scopes, priority, and concurrency.
- **Quota**: how much of a resource may be consumed in a defined window.
- **Reservation**: temporary capacity held before execution and released or committed afterward.
- **Usage**: actual consumed resource, distinct from reserved capacity.
- **Budget**: economic ceiling, intentionally separate from quota.
- **Policy**: conditions under which an entitlement may be exercised.
- **Ledger**: append-oriented accounting/evidence record for decisions and consumption.

## Initial resource dimensions

`requests`, `tokens`, `compute_units`, `concurrent_jobs`, `workers`, `storage_bytes`, and `bandwidth_bytes`.

Initial windows: `minute`, `hour`, `day`, and `month`.

## Decision model

- `ALLOW`: requested usage fits the entitlement.
- `THROTTLE`: execution should wait because a concurrency constraint is active.
- `DENY`: a hard quota boundary would be exceeded.

A decision must identify the principal, entitlement tier, reason, timestamp, and reservation when one is created.

## Reservation model

```text
request
  -> evaluate
  -> reserve
  -> execute
  -> commit(actual usage)
       or
  -> release
```

Reservations expire automatically so abandoned work does not permanently consume capacity.

## Security requirements for the next layer

1. API keys are generated with cryptographic randomness.
2. Raw API keys are shown only at creation/rotation time.
3. Stored key material is hashed/peppered; plaintext keys are never committed to Git.
4. Key scopes cannot exceed the principal's entitlement.
5. Revoke/rotate operations are auditable.
6. Quota cannot be disabled through negative, zero, or unbounded user input.
7. Provider credentials remain behind provider adapters and are never exposed as Research OS API keys.

## Persistence boundary

The foundation module is deliberately persistence-agnostic. A later adapter may persist principals, keys, reservations, usage, and ledgers in the canonical Research OS storage layer. It must not duplicate identity or create a parallel lifecycle.

## API surface planned

```text
POST /v1/keys
GET  /v1/keys
POST /v1/keys/{id}/rotate
POST /v1/keys/{id}/revoke
GET  /v1/quota
GET  /v1/usage
GET  /v1/entitlements
```

Exact HTTP contracts will be added only after the repository's existing identity/session contracts are reconciled with this model.

## Lifecycle rule

Implementation branches must start from the current canonical generation. Validation is performed before any owner-authorized merge. A merge creates a new generation; the new generation requires its own post-merge verification.
