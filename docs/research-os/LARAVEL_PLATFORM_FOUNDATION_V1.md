# Research OS Laravel Platform Foundation

- Document ID: ROS-LARAVEL-PLATFORM-FOUNDATION
- Version: 1.0.0
- Status: Proposed for integration
- Baseline: main

## Purpose

Define Laravel as a long-lived Research OS Platform component. Laravel integrates with the existing Research OS Platform; it does not replace or duplicate it.

## Non-goals

- No replacement of the existing Platform.
- No direct Engine-to-Runner execution path.
- No client-side security authority.
- No duplicate capability when an existing canonical capability already exists.
- No bypass of the Unified Final Gate.

## Responsibilities

1. HTTP/API boundary and protocol adaptation.
2. Identity/context propagation.
3. Authorization integration without overriding canonical decisions.
4. Workflow command/query integration.
5. Queue/event integration.
6. Tool gateway integration.
7. Evidence and audit integration.
8. Health, readiness, diagnostics and observability.
9. Versioning and compatibility management.
10. Administrative/control-plane APIs.

## Canonical execution path

Client -> Laravel Platform API -> authorization/policy boundary -> workflow command -> event/queue -> stateless worker -> execution -> evidence -> audit.

## Modules

Core, Identity, Authorization, Workflow, Messaging, Tools, Evidence, Audit, Operations, Configuration, Versioning and Control.

## Reliability

Every externally-triggered operation defines correlation ID, idempotency behavior, timeout behavior, retry policy, terminal failure behavior and evidence/audit behavior.

Resource conflicts fail closed. A rejected version stops execution and reconciles/releases resources according to canonical workflow policy; it never overwrites another valid version.

## Security boundary

Identity -> Capability -> Policy -> Authorization -> Entitlement -> Execution -> Evidence.

Laravel transports and adapts these decisions but cannot manufacture an ALLOWED decision on behalf of another authority.

## Compatibility

- Stable public contracts are versioned.
- Adapters isolate implementation changes.
- Existing Platform contracts are preferred over new equivalents.
- Breaking changes require a new contract version and migration plan.
- Old snapshots are preserved according to repository versioning rules.

## Delivery phases

1. Foundation and contracts.
2. Laravel runtime skeleton.
3. Platform adapters.
4. API surface.
5. Messaging/workflow integration.
6. Evidence/audit/observability.
7. Client integration.
8. Failure/recovery qualification.
9. Unified Final Gate and merge.

Implementation may be marked DEFERRED only when its boundary and contract are already defined and the deferral is recorded.
