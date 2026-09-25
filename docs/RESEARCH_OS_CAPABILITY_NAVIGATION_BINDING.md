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

Only proven identities are promoted into navigation metadata.

| Navigation destination | Index | Capability ID | Authority | Status |
|---|---:|---|---|---|
| Agent Center | 2 | `agent` | canonical capability registry | BOUND |
| GitHub | 5 | `github` | canonical capability registry | BOUND |
| Friend Connect | 13 | `friend` | canonical capability registry | BOUND |
| Workflows | 15 | `factory_v3` | canonical capability registry | BOUND |
| Control Center | 16 | `control_center` | canonical capability registry | BOUND |
| Owner | 17 | `owner` | Owner Experience contract | BOUND |

The Owner row is intentionally different: Owner is an authority identity, not a
replacement entry in the executable capability registry. Its identity is
server-derived and the system-level Owner role is unrestricted by resource or
scope.

The remaining navigation destinations stay explicitly unbound until a
canonical capability owner, authorization boundary, evidence path, and
verification coverage are proven. They remain **HOLD**, never implicit
permission.

The executable convergence contract is
`current/RESEARCH_OS_CAPABILITY_CONVERGENCE_CONTRACT.json`, validated by
`tools/validate_research_os_capability_convergence.py`.

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

The convergence validator and Flutter binding test verify:

1. the single navigation registry still contains exactly 18 destinations;
2. indexes remain exactly 0–17;
3. bound capability IDs are unique;
4. each promoted capability exists in the canonical capability registry;
5. Owner identity resolves through the Owner Experience contract rather than
   being fabricated as a backend capability;
6. unbound destinations remain HOLD and cannot be interpreted as authorization;
7. capability metadata remains identity-only and cannot grant, authorize, or
   execute anything.

## Promotion rule

A destination should receive a capability identity only after the capability
has a canonical owner, contract, implementation boundary, authorization
boundary, evidence path, and verification coverage.

This keeps the migration incremental and prevents the UI from becoming a
second authority system.
