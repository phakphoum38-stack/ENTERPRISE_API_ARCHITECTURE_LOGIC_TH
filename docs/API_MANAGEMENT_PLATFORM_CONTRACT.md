# Research OS API Management Platform Contract

## 1. Purpose

The API Management Platform is the product/management layer used to create, publish, secure, govern, observe, and consume Research OS APIs.

It is distinct from the runtime API implementation. The management layer must not replace or duplicate the existing execution-control kernel.

## 2. Canonical boundary

```text
Developer / Owner
        |
        v
API Management Platform
  |  Projects / Applications
  |  APIs / Versions / Endpoints
  |  Keys / Scopes / Plans
  |  Docs / Explorer / Webhooks
  v
ResourceControlPlane
  v
Authentication -> Authorization -> Entitlement -> Policy
  -> Quota -> Budget -> Admission -> Routing
  v
Execution
  v
Usage / Cost -> Evidence / Audit
```

The existing `APIKeyManager`, `ResourceGovernance`, `PolicyEngine`, `BudgetLedger`, `ResourceAdmissionGate`, `GovernedAgentRouter`, usage ledger, and evidence chain remain authoritative execution primitives.

## 3. Domain model

### Organization
Top-level ownership and governance boundary.

### Project
A bounded product/workspace under an organization. Projects own applications and API products and provide an administrative scope.

### Application
A consumer integration owned by a project. Applications receive credentials and consume one or more API products.

### Developer / Service Account
A human or non-human principal operating an application. Authentication identity is separate from provider credentials.

### API
A managed logical API exposed by Research OS. An API is a catalog/product object and does not itself execute requests.

### API Product
A consumable packaging of one or more API capabilities, versions, scopes, and entitlement requirements.

### API Version
A versioned contract of an API. Versioning is independent from the Research OS product release version.

### Endpoint
A managed operation with method, path, request/response contract metadata, required scopes, policy hooks, and routing metadata.

### Scope
An authorization capability string. Scope grants must be evaluated together with principal, application, entitlement, and policy.

### API Key
A credential bound to an application/principal and a set of scopes. Raw credentials are returned only at creation/rotation time and are never persisted as plaintext.

### Plan
A reusable commercial/operational policy bundle. A plan references entitlements rather than implementing quota or budget logic itself.

### Entitlement
The effective permission/capacity grant used by the existing resource-governance/admission system.

### Quota / Rate Limit
Administrative policy describing resource ceilings and request-rate behavior. Enforcement is delegated to existing governance/admission primitives.

### Budget
Administrative spending/resource ceiling. Enforcement is delegated to the existing budget/admission path.

### Gateway / Route
Managed routing metadata that selects the runtime service/provider/agent boundary after authorization and admission succeed.

### Usage / Cost
Observable execution measurements. Existing usage ledger remains the source of execution accounting.

### Audit Event
Administrative/security lifecycle event. Audit records must not be confused with execution evidence or authority grants.

### Webhook
A managed outbound notification subscription for defined lifecycle/usage events. Delivery must be bounded, authenticated, replay-safe, and auditable.

### Documentation / API Explorer metadata
Presentation and discovery metadata derived from the managed API contract. Documentation is not an authorization mechanism.

### SDK metadata
Machine-readable generation metadata derived from the same API contract. SDK generation must not create a second API definition.

## 4. Relationships

```text
Organization
  |
  +-- Project
       |
       +-- Application ---- APIKey ---- Scope
       |
       +-- API Product ---- Entitlement ---- Plan
       |       |
       |       +-- API ---- Version ---- Endpoint
       |
       +-- Webhook

Request
  -> Authentication
  -> Authorization
  -> Entitlement
  -> Policy
  -> Quota / Rate Limit
  -> Budget
  -> Admission
  -> Route
  -> Execution
  -> Usage / Cost
  -> Evidence / Audit
```

## 5. Invariants

1. Management metadata cannot grant authority by itself; execution authorization remains governed by the runtime control plane.
2. No second API-key verifier may be introduced.
3. No second quota, policy, budget, reservation, usage, or evidence engine may be introduced.
4. Provider credentials remain separate from consumer API keys.
5. Raw API keys must never be persisted in plaintext.
6. Scope assignment is explicit and must be validated against effective entitlement.
7. API/version/endpoint identifiers are stable management identities and are not derived from display names.
8. API versioning is independent from application/product release versioning.
9. Usage records are measurements; evidence records establish execution/provenance facts; neither independently grants authority.
10. Audit events describe administrative/security lifecycle events and must retain actor, target, action, timestamp, and outcome where applicable.
11. Public/network exposure is not implied by defining the management contract.
12. Any production exposure must add an explicit security boundary including authentication, authorization, TLS, request-size/rate controls, auditability, and network policy.

## 6. Capability classification

| Capability | Current status | Canonical existing boundary | Management-layer gap |
|---|---|---|---|
| API key create/verify/revoke/list | IMPLEMENTED_KERNEL | `APIKeyManager` | management HTTP/resource model |
| API key durable persistence | PARTIAL | `APIKeyStore` + in-memory adapter | durable adapter |
| API key rotation | MISSING | `APIKeyManager` | lifecycle operation + atomic replacement semantics |
| Principal registration | IMPLEMENTED_KERNEL | `ResourceControlPlane` | management resource model |
| Entitlement/scopes | IMPLEMENTED_KERNEL/PARTIAL | governance + policy | administrative CRUD contract |
| Quota | IMPLEMENTED_KERNEL | `ResourceGovernance` | management CRUD/visibility |
| Rate limiting | PARTIAL | governance primitives | explicit API-management policy model |
| Budget | IMPLEMENTED_KERNEL | `BudgetLedger` | management CRUD/visibility |
| Admission | IMPLEMENTED_KERNEL | `ResourceAdmissionGate` | do not duplicate |
| Routing | IMPLEMENTED_KERNEL | `GovernedAgentRouter` | managed route/catalog metadata |
| Usage ledger | IMPLEMENTED_KERNEL | hash-chained usage ledger | query/aggregation API |
| Evidence chain | IMPLEMENTED_KERNEL | hash-chained evidence | management visibility only |
| API catalog/registry | MISSING | existing runtime OpenAPI is contract surface | management registry |
| Project/application model | PARTIAL | Protocol 10 project contract / identity surfaces | API-management ownership model |
| API/version/endpoint catalog | PARTIAL | OpenAPI V1/V2 runtime contract | managed catalog lifecycle |
| Developer portal | MISSING | none | portal/explorer surface |
| Webhooks | MISSING | none | subscription/delivery contract |
| SDK generation metadata | MISSING | OpenAPI can be source | generation contract |
| Audit management API | PARTIAL | evidence/governance traces | dedicated administrative audit surface |
| Production external security boundary | MISSING | local-first API today | explicit deployment/security contract |

## 7. Management namespace direction

The management API must be reconciled with the existing `/v1` runtime API rather than silently replacing it.

Recommended separation:

```text
/v1/...                 runtime/consumer API
/v1/management/...      administrative API management surface
```

The final namespace must be validated against the existing OpenAPI contract before implementation. No existing runtime route is to be repurposed merely to fit the management model.

## 8. Lifecycle examples

### API publication

```text
Create API
 -> create version
 -> register endpoint contract
 -> attach scopes/policies
 -> attach route metadata
 -> publish API product
 -> expose documentation/explorer
```

### Credential lifecycle

```text
Create application
 -> create API key
 -> bind scopes
 -> validate entitlement
 -> return raw secret once
 -> verify through APIKeyManager
 -> revoke/rotate through managed lifecycle
```

### Request lifecycle

```text
API request
 -> identify principal/application
 -> verify API key
 -> authorize scopes
 -> resolve entitlement
 -> evaluate policy
 -> enforce quota/rate limit
 -> enforce budget
 -> reserve/admit
 -> route
 -> execute
 -> commit usage/cost
 -> append evidence/audit
 -> release on failure
```

## 9. Non-goals for this contract slice

- No replacement of `ResourceControlPlane`.
- No new provider abstraction.
- No public-network deployment.
- No workflow modifications.
- No release/authority automation.
- No mutation of historical baselines or fixtures.
- No implementation of every management feature in one change.

## 10. Next implementation slices

1. Canonical management domain types + invariants.
2. API/project/application registry boundary.
3. Management OpenAPI contract reconciled with current runtime OpenAPI.
4. Durable API-key store + explicit rotation semantics.
5. Administrative plan/entitlement/quota/budget APIs over existing kernel.
6. Usage/cost/audit query surfaces.
7. Developer portal/explorer metadata.
8. Webhook and SDK contracts.
9. External deployment security boundary.

Each slice must remain independently reviewable and must not weaken existing governance or evidence gates.
