# Research OS Platform — Capability & Continuation Status

> Purpose: This document is the continuation map for the Research OS / AEOS platform.
> It records what has already been designed or implemented, what boundary each component owns,
> and what remains to be continued so future work does not require searching through old conversations.

## 1. Core architecture — locked direction

The platform follows:

```
UI / Clients
    ↓
Agent Runtime
    ↓
AEOS Authority
    ↓
External Tools / Stateless Runners
    ↓
Evidence
    ↓
AEOS Recheck
    ↓
Final Gate
    ↓
Release / EXE
```

Core production model:
- Event-driven
- Queue-based
- Stateless Runner
- Horizontally scalable workers
- Durable delivery / recovery
- AEOS as policy, identity, lineage, evidence and gate authority
- Agent Runtime as orchestration/execution/recovery, not authority
- External Flutter tooling remains separate from the main Research OS UI
- User-facing installation is via release artifact/EXE; local setup is optional, not a required production flow

## 2. Authority boundaries

### AEOS
AEOS owns:
- Identity
- Authorization / capability policy
- Lineage
- Evidence requirements
- Gate decisions
- SHA/base/head verification
- Repair scope approval
- Blocking conditions
- Final recheck

AEOS rules:
- NO EVIDENCE != PASS
- WAITING != PASS
- OLD SHA PASS != NEW SHA PASS
- UNKNOWN != PASS
- UNLINKED FILE = BLOCK
- Every failure must identify file/path, fail code and evidence
- Structural/lineage/identity failures do not get delegated to FlutterFixCode

### Agent Runtime
Agent Runtime owns:
- Task orchestration
- Queue/task scheduling
- Agent handoff
- Retry policy
- Lease/recovery
- Checkpoint/resume
- Cancellation
- Execution coordination
- Evidence collection
- Runtime status

Agent Runtime does NOT own:
- Final authorization
- Lineage authority
- Scope expansion
- Final PASS
- Release approval

### FlutterFixCode
FlutterFixCode is a repair executor boundary.
It receives only an AEOS-approved repair request.
It does not:
- choose its own target file
- expand repair scope
- bypass lineage
- declare PASS
- release artifacts
- replace AEOS

## 3. Already implemented / existing work

### 3.1 Research OS Final Gate
Existing workflow:
- `.github/workflows/research-os-final-gate.yml`
- Python compile/test/recovery/static smoke checks
- Flutter contract/analyze/test/build smoke checks

### 3.2 Owner Flutter Code Tool lifecycle
PR #549:
- Owner-only code lifecycle
- Select project/file
- Read/edit
- Unified diff preview
- SHA/TOCTOU protection
- Flutter analyze/test through external toolchain
- Automatic rollback on validation failure
- Evidence persistence
- Source remains in `apps/research_os_flutter`
- Flutter repository remains an external tool

### 3.3 AEOS workflow current-head fix
PR #550:
- Resolves the current PR head instead of trusting a stale workflow-run commit

### 3.4 Resource conflict / version lineage
PR #551:
- Resource version store
- Atomic stale-version rejection
- Conflict evidence
- Historical branch versions
- Release/reconcile callback
- No overwrite of another version within the same version lineage

### 3.5 Stateless Worker Pool
PR #552:
- Durable event delivery
- Bounded worker pool
- Claim/handler/ACK
- No ACK on handler exception
- Recovery-oriented execution

### 3.6 DLQ + Retry / Event Delivery
PR #553:
- Durable delivery / retry work
- Current head after fixes:
  `327088c0a2add1f1f48cf7327e054dfcec1fe20d`
- Fixed delivery SELECT/Delivery constructor column mismatch
- Important: always verify the current head; an older SHA previously failed the V3 regression

### 3.7 Control Center integration
PR #554:
- Latest head: `30480418302a5ae9f98fbf458bbd3f2cf8d2b0f5`
- Removed a redundant Flutter analyzer type check in `native_control_center_page.dart` that was failing current CI
- Flutter native Control Center
- Orchestration APIs
- Owner authorization
- Resource lineage
- Worker pool
- DLQ/retry
- Governed runtime
- Final Gate evidence/validator
- API v2 compatibility

### 3.8 Generic AEOS file lineage verifier
PR #556:
- Branch: `feat/aeos-generic-file-lineage-gate`
- Head: `9ba21d24015a4ba48e60b529aaa7270888070bbd`
- Adds fail-closed changed-file lineage classification
- Supports MODIFIED, RENAMED, COPIED, ADDED_WITH_LINEAGE, ADDED_GENESIS, ORPHAN_ADDED
- Requires explicit predecessor/genesis evidence for new files
- Produces structured path/fail-code/SHA/evidence records
- Includes unit coverage for modified, orphan, genesis and rename cases

### 3.9 AEOS one-shot comprehensive review
Existing workflow:
- `.github/workflows/aeos-one-shot-auto-merge.yml`
- Resolves exact PR/head
- Fetches trusted main
- Verifies exact target SHA
- Runs PR checks
- Runs comprehensive review
- Verifies certificate and merge authority conditions
- Uploads review evidence

Known next improvement:
- Generic file lineage verification for every changed file
- Do not rely on filename-only matching
- Require existing lineage, rename/move/copy lineage, explicit predecessor, or explicit genesis declaration

### 3.10 FlutterFixCode Adapter
External Flutter repository:
- `phakphoum38-stack/flutter`
- PR #5
- Branch: `feature/aeos-flutter-repair-adapter`
- Head: `cda2bd0469ec6a4e90b35e453429c222097979ea`

Implemented:
- Repair request validation
- Required AEOS context validation
- Repairable vs blocked failure classification
- Scope enforcement
- SHA validation
- Deterministic repair envelope
- Tests
- Documentation

Repairable examples:
- `AEOS-CODE-FAIL`
- `AEOS-TEST-FAIL`
- `AEOS-STATIC-ANALYSIS`
- `AEOS-FLUTTER-ANALYZE`
- `AEOS-FLUTTER-TEST`

Blocked examples:
- `AEOS-LINEAGE-ORPHAN`
- `AEOS-SHA-MISMATCH`
- `AEOS-MISSING-EVIDENCE`
- `AEOS-IDENTITY-CONFLICT`
- `AEOS-WORKFLOW-LINEAGE`

Important:
The adapter is an execution boundary, not a source of authority.

## 4. UI / Control Center target

The Control Center should expose the complete operational state:

### AEOS Overview
- System status
- Current SHA
- Base SHA
- Gate status
- Active failures

### Inspection
- Identity
- Authorization
- Lineage
- Evidence
- Workflow
- Final Gate

### Repair Center
- Failure inbox
- Repair queue
- Repair request detail
- Allowed files
- Repair scope
- Attempts
- Recheck status
- Repair history

### FlutterFixCode Monitor
Read-only operational display:
- Current job
- Current step
- File
- Symbol / line
- Fail code
- Evidence
- Current SHA
- Base SHA
- Lineage
- Runtime/worker
- Timeline

It must show where execution stopped and where it failed.
It must not become a second authority or bypass AEOS.

### Agent Runtime Monitor
- Active agents
- Queue
- Running tasks
- Waiting tasks
- Repair tasks
- Blocked tasks
- Worker/lease state
- Checkpoint
- Recovery
- Retry/attempt

### Release
- Recheck
- Final Gate
- Build
- Packaging
- Artifact
- EXE
- Release history

## 5. Client surfaces to add/continue

All clients must use the same Agent Runtime + AEOS contract.

### Control Center
Primary operational UI.

### VS Code Extension
Developer-facing view:
- Current project/branch/SHA
- AEOS diagnostics
- Lineage
- Repair status
- Agent status
- Gate status
- Evidence links
- Diff/impact inspection

The extension must not create a parallel workflow.

### CLI
Automation/power-user surface:
- `aeos status`
- `aeos inspect`
- `aeos lineage`
- `aeos repair status`
- `aeos agent status`
- `aeos gate status`
- `aeos evidence`

### GitHub integration
PR status should expose:
- Identity
- Lineage
- Evidence
- Tests
- Repair
- Recheck
- Final Gate

## 6. Additional platform functions identified

These are the capability backlog, not all implemented yet.

### Platform
- Project/workspace manager
- Environment selector
- Project health
- Agent Registry
- Tool Registry
- Capability Manager
- Plugin SDK
- Extension registry

### Agent Runtime
- Planning
- Task decomposition
- Agent handoff
- Context snapshots
- Deadlock detection
- Timeout
- Cancellation
- Scheduler
- Lease manager
- Checkpoint/resume
- Recovery
- Run replay

### Code Intelligence
- Code search
- Symbol search
- Dependency graph
- Impact analysis
- Diff viewer
- History/blame
- Lineage viewer
- Generated-code detection
- Duplicate-code detection

### Repair
- Failure classification
- Repair request
- Scope enforcement
- Patch preview
- Attempt tracking
- Retry
- Rollback
- Recheck
- Repair history

### Testing
- Unit
- Integration
- E2E
- Regression
- Static analysis
- Security scan
- Performance
- Flaky-test detection

### Governance
- Owner controls
- Approval workflow
- Policy engine
- Capability controls
- Resource authorization
- Version conflict handling
- Immutable evidence
- Audit trail

### Observability
- Logs
- Metrics
- Traces
- Agent health
- Runner health
- Queue health
- Tool health
- Failure heatmap
- SLA monitoring

### Security
- Secret/environment manager
- Credential isolation
- Token rotation
- Permission audit
- Sandbox
- Tool allowlist
- Network policy
- Artifact integrity
- Supply-chain verification

### Release
- Build matrix
- Artifact registry
- Version management
- Release notes
- Signing
- Packaging
- Installer/EXE
- Release rollback
- Release history

### Operations
- Dry run
- Impact analysis
- Incident mode
- System self-diagnostics
- Notification hub
- Cost/resource monitoring

## 7. Recommended continuation order

1. Stabilize and verify current PR heads/CI
2. Finish generic AEOS file-lineage verification
3. Integrate repair request lifecycle with Agent Runtime
4. Add read-only FlutterFixCode status monitor
5. Expand Control Center with Repair + Agent Runtime views
6. Add evidence/timeline/replay
7. Add VS Code Extension
8. Add GitHub PR status integration
9. Add Plugin/Tool/Agent registries
10. Add dry-run and impact analysis
11. Harden security/secret/sandbox boundaries
12. Complete build/package/release/EXE path
13. Final Gate integration
14. Production validation

## 8. Continuation rule

Before starting new work:
- Read this document first.
- Check the referenced PR/branch/head SHA.
- Check current workflow runs for the exact head.
- Do not assume an old SHA represents the current state.
- Do not duplicate work that already exists in main.
- Keep external Flutter source separate from Research OS UI.
- Return state/evidence/results to the main platform and Final Gate.
- Any repair must follow:
  `FAIL → Repair Request → FlutterFixCode → New SHA → AEOS Lineage → AEOS Recheck → PASS/WAITING/FAIL`

## 9. Current user-facing principle

The user should not need to:
- clone the repository
- install Flutter locally
- run Python locally
- run repair commands locally
- manually chase workflow runs

The intended experience is:

```
Control Center / VS Code / GitHub
            ↓
       Agent Runtime
            ↓
           AEOS
            ↓
      Repair / Tools
            ↓
       Recheck / Gate
            ↓
          Release
            ↓
        Download EXE
```

Local development remains optional for developers/owners, not a required production/user workflow.

## 10. Status legend

- ✓ IMPLEMENTED / EXISTS
- → INTEGRATION / CONTINUE
- ⏳ PLANNED
- ⚠ NEEDS VERIFICATION
- ✗ BLOCKED / FAILED

This file is a continuation map, not a replacement for source-of-truth code, AEOS evidence, PR state, or Final Gate results.
