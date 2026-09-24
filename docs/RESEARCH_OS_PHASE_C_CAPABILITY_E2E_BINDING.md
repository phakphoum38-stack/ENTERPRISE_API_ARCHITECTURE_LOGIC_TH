# Research OS Phase C — Capability E2E Binding

## Purpose

Phase C closes the remaining binding gap identified after Phase A delegation
and Phase B lifecycle/evidence work.

Canonical path:

Command → external authorization → existing executor → observation → Phase B evidence → terminal state

This phase does not introduce a second runtime, command bus, scheduler,
authorization authority, or release authority.

## Canonical bindings

- Friend → FriendRuntimeContract
- Agent → AgentRuntime
- GitHub → read-only github_status.py
- Factory V3 → FactoryExecutionEngine
- Assurance → EvidenceRecorder, evidence authority only

Operation identity comes from tools/capability_delegation.py. Phase C does not
create a second operation mapping.

## Authorization boundary

CapabilityE2EBinding.invoke() accepts authorization from the canonical boundary.
It never grants authorization itself. Mutation operations therefore cannot run
when authorization is false.

## Evidence and recovery

Every invocation starts at INTENT and ends at COMPLETE or RECOVER. Evidence is
append-only and bound to owner, correlation ID, source SHA, target SHA, workflow
run, and contract version.

Executor exceptions become terminal RECOVER evidence. Unknown capabilities,
unsupported operations, and missing executor methods fail closed.

## Phase C completion criteria

1. All five canonical partial capabilities have a binding path.
2. Friend/Agent/Factory mutation paths cannot bypass authorization.
3. GitHub remains read-only.
4. Assurance cannot become an execution capability.
5. Unknown capability/action/executor fails closed.
6. Every path produces terminal lifecycle evidence.
7. Exact source SHA and correlation remain bound through recovery.

The Unified Final Gate remains the only release authority.
