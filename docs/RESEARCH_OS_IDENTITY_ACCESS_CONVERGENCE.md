# Research OS — Identity / Access Convergence

Wave 1 records the existing identity and access boundary as a platform contract.

The existing server session remains the source of identity. The canonical Flutter surface only observes the verified result. The existing policy and approval boundaries remain outside Flutter, and execution remains delegated to the existing runtime.

## Owner invariant

Owner identity is derived from the server status endpoint. Owner is the highest privilege and is not constrained by resource or scope. Client or UI input cannot grant that authority.

## Canonical surface

The existing Google Sign-In destination is the presentation entry for the identity flow. Its capability identifier is metadata only; it does not grant permission.

## Boundaries

- Server session verification remains authoritative.
- Identity context remains server-derived.
- Existing OwnerPolicy remains the policy boundary.
- Approval remains an external approval boundary.
- Execution remains in the existing orchestrator/runtime.
- No new runtime, policy authority, or navigation registry is introduced.

## Verification

The contract is bound to the Unified Final Gate before release authority can pass.
