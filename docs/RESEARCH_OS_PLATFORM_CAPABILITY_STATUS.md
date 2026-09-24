# Research OS Platform — Capability & Continuation Status

> Baseline: `main` @ `436214890e922fa8c5262cd7bc2b98a54aa1a06a`
>
> This is a continuation map only. Source code, workflow evidence, PR state, contracts, and Final Gate remain authoritative.

## 1. Locked architecture

```
Clients / Control Center
        ↓
Capability Registry
        ↓
Authorization / Owner boundary
        ↓
Agent Runtime / Workflow
        ↓
Event → Queue → Stateless Runner
        ↓
Evidence / Provenance
        ↓
AEOS Recheck
        ↓
Single Final Gate
        ↓
Release / Artifact
```

Rules:
- Event-driven, queue-based, stateless runners with horizontal scaling.
- Runtime/orchestration is not authorization or release authority.
- Final Gate remains the single release authority.
- Evidence is immutable and must bind identity, execution context and exact SHA.
- Unknown, missing, stale or conflicting evidence fails closed.
- Resource conflict is REJECT: stop execution, release resources, ACK/reconcile delivery; never overwrite another same-version state.
- Alternate versions may branch.
- External Flutter tooling remains separate from the Research OS UI.
- Production user flow should consume the packaged release artifact; local setup is optional.

## 2. Current main milestones

### Merged and current
- PR #560 — shared navigation/sidebar registry compile and platform-surface parity.
- PR #561 — trusted Research OS session → Developer Platform identity gateway.
- PR #562 — generic AEOS file-lineage gate.
- PR #563 — canonical platform contract.
- PR #564 — exact-SHA release spine gate.

Current main head: `436214890e922fa8c5262cd7bc2b98a54aa1a06a`.

### Navigation contract
The canonical Research OS application surface uses one navigation registry for Windows/Desktop and Web/iOS/Mobile. The registry contains the 15 stable destinations (indexes 0–14) and platform surfaces consume the same source of truth.

Do not create separate platform menu lists. Do not expose Workflow, Evidence, Final Gate or Owner as standalone navigation destinations until their real capability/page contracts exist.

## 3. Authorization and identity

Owner is the highest privilege and is not constrained by resource/scope boundaries used by other roles.

The trusted Developer Identity Gateway derives the Developer principal from a verified Research OS session and mints a short-lived server-side assertion. Client code must not supply Owner identity, role, signing secret, timestamp, nonce or signature.

Developer execution remains subject to authorization, grant/resource ownership, SHA/version checks and fail-closed security boundaries.

## 4. Canonical platform contract

The current contract governs:
- identity and idempotency
- versioning and exact SHA binding
- state machine and terminal-state rules
- resource conflict handling
- bounded retry
- reconciliation after uncertainty/worker loss/conflict
- immutable evidence
- provenance
- observability/correlation
- compatibility
- recovery
- fail-closed behavior

The contract does not create a second executor, scheduler, queue, authority or Final Gate.

## 5. Current operational lifecycle

```
FAIL
  ↓
Repair Request
  ↓
Approved repair boundary
  ↓
External tool / Stateless Runner
  ↓
New SHA
  ↓
Lineage verification
  ↓
AEOS recheck
  ↓
PASS / WAITING / FAIL
```

A repair executor cannot expand scope, bypass lineage, declare release PASS, or replace AEOS authority.

## 6. Research OS application surface

Current target surface:

- Home
- AI Chat
- Agent Center
- Brain Skills
- Library
- Knowledge Graph
- GitHub
- Google Workspace
- Friend Connect
- Local API & Service
- System Monitor
- Settings
- Developer Access
- Google Sign-In
- Control Center

The same capability/navigation contract must feed Windows/Desktop, Web and iOS/Mobile.

Control Center remains the canonical operational surface. It may observe identity, authorization, lineage, evidence, workflow, runtime and release state, but observation/navigation does not itself grant authority.

## 7. Capability backlog

### Platform
- Project/workspace manager
- Environment selector
- Agent Registry
- Tool Registry
- Capability Manager
- Plugin/extension boundary

### Agent Runtime
- Planning and task decomposition
- Agent handoff
- Context snapshots
- Deadlock/timeout/cancellation handling
- Lease/checkpoint/recovery
- Replay

### Code intelligence
- Code/symbol search
- Dependency and impact analysis
- Diff/history/lineage inspection
- Generated/duplicate-code detection

### Repair
- Failure classification
- Repair request lifecycle
- Scope enforcement
- Preview
- Attempt/retry
- Rollback
- Recheck
- Repair history

### Testing / assurance
- Unit
- Widget/integration
- E2E
- Regression
- Static/security/performance checks
- Flaky-test detection

### Governance / security
- Owner controls
- Approval/policy/capability controls
- Resource authorization
- Immutable audit/evidence
- Secret isolation
- Sandbox/tool allowlist
- Network policy
- Artifact/supply-chain integrity

### Release
- Build matrix
- Artifact registry
- Versioning
- Signing
- Packaging/installer
- Rollback
- Release history

## 8. Next execution order

1. Keep current main green and exact-SHA governed.
2. Build the shared Research OS test helpers for navigation/surface contracts.
3. Complete state/lifecycle contract coverage:
   `Idle → Load Projects → Select File → Read → SHA → Edit → Preview → Apply → Validate → Evidence`.
4. Add explicit stale-SHA/resource-conflict integration coverage.
5. Extend the canonical Control Center with read-only Repair and Agent Runtime monitoring.
6. Bind evidence/timeline/replay views to existing authoritative data.
7. Continue the single capability registry → authorization → navigation → feature/page path.
8. Harden the Windows single-distribution release path containing the required Research OS runtime/tooling components.
9. Run the unified Final Gate against the exact release SHA.

## 9. Continuation rules

Before new work:
- Use current `main` as the baseline.
- Verify the exact PR/head SHA and current workflow runs.
- Do not revive an old SHA as if it were current.
- Do not duplicate work already merged into `main`.
- Keep external Flutter tooling separate from Research OS UI.
- Do not add placeholder authority/navigation surfaces.
- Return state, evidence and results to the canonical platform and single Final Gate.
- Leave unrelated deferred failures deferred unless a current gate proves they are on the active path.

## 10. User-facing target

```
Research OS / Control Center / Web / Mobile / Desktop
                     ↓
              Capability + Auth
                     ↓
               Agent Runtime
                     ↓
             Queue / Runner
                     ↓
              Evidence / AEOS
                     ↓
                Final Gate
                     ↓
                 Release
                     ↓
              Download / Install
```

The goal is that production users do not need to clone the repository, install Flutter/Python, or manually chase workflow runs.

Status legend:
- ✓ IMPLEMENTED / MERGED
- → CONTINUE
- ⏳ PLANNED
- ⚠ VERIFY
- ✗ BLOCKED
