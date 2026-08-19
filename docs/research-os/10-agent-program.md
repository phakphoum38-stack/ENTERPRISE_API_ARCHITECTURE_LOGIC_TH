# Research OS — 10-Agent Execution Program

## Mission

Complete Research OS as one coherent product: API, runtime, queue/worker execution, tools, workflows, reliability, security/observability, GUI/UX, application packaging, and integration QA.

## Architecture rule

The 10 workstreams share one architecture contract. No agent may redefine public contracts, duplicate a subsystem, or silently introduce a second implementation of an existing capability.

All work follows:

`Inspect → Plan → Implement → Test → Evidence → Integrate → Gate`

## Workstreams

| ID | Agent | Scope | Definition of Done |
|---|---|---|---|
| A01 | API | OpenAPI, endpoints, contracts, compatibility | Every required endpoint maps to implementation, auth boundary, tests, and evidence |
| A02 | Core Runtime | orchestrator, execution lifecycle, state machine | Runtime lifecycle is deterministic, restart-safe, and tested |
| A03 | Queue/Worker | queue, lease, heartbeat, retry handoff, DLQ, worker pool | No lost work; stale work is detectable and recoverable |
| A04 | Tools | registry, discovery, execution, lifecycle | Every supported tool is registered, versioned, tested, and observable |
| A05 | Workflow | GitHub Actions, validators, gates, automation | Canonical workflows are valid, non-duplicated, and gated |
| A06 | Reliability | timeout, retry, idempotency, recovery, backpressure | Failure modes have explicit recovery behavior and tests |
| A07 | Security/Observability | auth, secrets, audit, logs, metrics, tracing | Security boundaries and operational signals are testable |
| A08 | GUI/UX | app shell, navigation, dashboard, product pages | Product UI is coherent and connected to API contracts |
| A09 | App Packaging | application shell, icon, branding, installers/artifacts | Shippable application package; no Flutter branding/UI dependency |
| A10 | Integration/QA | E2E, regression, evidence, release gate | Full-system evidence passes before release |

## Architect / Lead

The Architect/Lead owns cross-agent contracts, dependency ordering, integration boundaries, and release decisions. The Lead does not replace implementation agents; it prevents conflicting implementations.

## UI constraint

Research OS GUI/UX is product UI owned by this repository. Flutter is **not** the required application UI technology and Flutter branding must not appear in the product icon or application shell.

## Dependency order

1. A01 establishes/validates contracts.
2. A02/A03 implement execution foundations against those contracts.
3. A04/A05/A06/A07 harden platform behavior.
4. A08 builds the UI against stable contracts; it may use mocks during parallel development.
5. A09 packages the application and branding.
6. A10 validates the integrated system and produces release evidence.

## Evidence standard

A workstream is not complete because code exists. Completion requires:

- implementation
- focused unit tests
- integration/E2E coverage where applicable
- workflow/CI evidence
- explicit failure-path coverage
- documented ownership and contract

## Current baseline

- Orchestrator validator baseline: `71a5029337b45e37fbc8d1c32c6f2671efed573c`
- Research OS gate repair: `311ece33bf42ba709dfdba44afc063f361623ddd`
- V3 Master 10x10 runtime evidence: Run `32233438403`

These baselines are evidence references, not permission to assume unverified components are complete.
