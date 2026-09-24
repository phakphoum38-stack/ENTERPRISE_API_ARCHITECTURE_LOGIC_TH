# Research OS Capability → Navigation Binding

Status: **ACTIVE / INCREMENTAL BINDING**

This contract closes one real cross-layer gap without creating a second
navigation registry or granting authority to the Flutter presentation layer.

## Canonical flow

```text
Capability Registry
      ↓
Capability identity
      ↓
Authorization boundary
      ↓
Navigation Registry
      ↓
Page / Feature
```

The existing `researchNavigationItems` registry remains the only global
navigation destination list. Capability metadata is attached to a destination
only when an existing canonical capability identity is already available.

## Current binding

| Navigation destination | Index | Capability ID | Status |
|---|---:|---|---|
| Control Center | 14 | `control_center` | BOUND |

The `control_center` identity is already declared by
`tools/control_center_capability_registry.py`. This change does not create
another executor, runtime, scheduler, authorization system, or navigation
registry.

Other destinations remain unchanged until their canonical capability identity
and authorization contract are proven. A missing binding is therefore not
silently interpreted as permission.

## Authority rule

`ResearchNavItem.capabilityId` is **identity metadata only**.

It does not:

- grant access;
- bypass authorization;
- execute a capability;
- contain credentials;
- replace the backend capability registry;
- replace Owner authorization;
- create a platform-specific navigation list.

Authorization remains outside presentation widgets and execution remains
delegated to the owning subsystem.

## Verification

The binding test verifies:

1. the navigation registry still contains exactly 15 destinations;
2. indexes remain exactly 0–14;
3. destination labels remain unique;
4. Control Center resolves to the canonical `control_center` capability ID;
5. capability IDs do not duplicate across bound destinations;
6. capability metadata is not treated as an authorization grant.

## Promotion rule

A destination should receive a capability identity only after the capability
has a canonical owner, contract, implementation boundary, authorization
boundary, evidence path, and verification coverage.

This keeps the migration incremental and prevents the UI from becoming a
second authority system.
