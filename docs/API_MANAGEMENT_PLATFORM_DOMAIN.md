# Research OS API Management Platform — Canonical Domain

This document defines the management-plane vocabulary for the API Management Platform. It does not replace the Research OS execution/control-plane kernel.

## Canonical hierarchy

```text
Organization
└── Project
    ├── Application / Service Account
    │   └── API Key
    │       └── Scope grants
    ├── API
    │   └── API Version
    │       └── Endpoint
    ├── API Product
    │   └── APIs
    ├── Plan
    │   └── Entitlements
    │       ├── Scopes
    │       ├── Quota
    │       ├── Rate Limit
    │       ├── Budget
    │       └── Policy references
    ├── Gateway Routes
    ├── Webhooks
    └── Developer Portal metadata
```

## Runtime boundary

```text
Management objects
      ↓
Authentication / Authorization
      ↓
ResourceControlPlane
      ↓
Policy → Quota → Budget → Admission → Routing
      ↓
Execution
      ↓
Usage / Cost → Evidence / Audit
```

Management records describe ownership, configuration and intent. They do not themselves authorize execution or manufacture evidence.

## Invariants

1. Every Project belongs to exactly one Organization.
2. Every Application, API, Plan and Webhook is scoped to one Project.
3. Every API Version belongs to exactly one API.
4. Every Endpoint belongs to exactly one API Version.
5. Endpoint scope references must resolve to declared Scope records.
6. API keys are credential records; raw key material is never a domain object.
7. An API key cannot grant scopes outside its effective entitlement.
8. Provider credentials are separate from API-key identity records.
9. Quota, rate-limit, budget and policy evaluation remain owned by the existing control-plane primitives.
10. Management state cannot by itself produce PASS, authority, evidence validity, or merge authorization.

## Lifecycle

Management entities may use explicit lifecycle state, but lifecycle state must not be confused with runtime admission state. For example, `API.active` means the management record is enabled; it does not bypass policy, quota, budget or admission checks.

## Deliberate gaps

The following are management-plane capabilities to implement after the contract slice:

- durable API-key store
- key rotation/replacement lifecycle
- API and endpoint registry/catalog
- Project/Application administration
- Plan and Entitlement administration
- quota/rate-limit administration mapped to existing primitives
- usage and cost query/read models
- audit query API
- developer portal and API Explorer metadata
- webhook delivery configuration and lifecycle
- SDK generation metadata
- production-facing authentication, TLS, network controls and request limits

These are gaps, not permission to duplicate the existing execution kernel.
