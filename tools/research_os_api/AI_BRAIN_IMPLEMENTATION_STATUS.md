# Research OS AI Brain — Implementation Status

Status document for the latest Brain implementation on `feature/v2-ai-brain-core`.
It supplements `AI_BRAIN_CORE.md`; where that document stops at Phase 8, this
file is the current source of truth for Phases 9-10 and the code-complete Brain
composition before the final analyze/build/test/connection pass.

## Brain composition

```text
User Goal
  -> Context Engine
  -> Brain Goal / Intent / Known-Unknown model
  -> Capability Graph
  -> Agent Registry
  -> Skill Registry + Domain Skill Packs
  -> Decision / Risk Engine
  -> AgentOrchestrator canonical task DAG
  -> SkillExecutor
  -> Tool Registry
  -> HardenedExecutionController
  -> Tool observation / checkpoint
  -> Evidence Verification
  -> Activity Ledger
  -> Learning / Experience Engine
```

AI Gateway remains below/alongside this control plane as the provider/model
inference layer. Changing OpenAI-compatible, Gemini, Anthropic or local provider
does not own or erase Research OS skills, task state, permissions, memory or
learning evidence.

## Phase 9 — Safe Learning / Experience

Contract: `brain-learning-experience-phase-9`

Implemented in `v2_learning_engine.py`.

- reuses the canonical append-only `ActivityLedger`; no second learning database
- learns from structured terminal task outcomes, not hidden chain-of-thought
- does not capture raw prompt/response transcripts
- sanitizes credential-shaped objective summaries, blockers, verification data
  and evidence references before persistence
- aggregates success/failure/blocked/verification outcomes by capability, Skill
  and Tool
- identifies recurring blockers and failure categories
- can generate review-only Skill/runbook refinement proposals
- never edits source code, SkillDefinitions, prompts, permissions or model weights
  automatically
- repeated observation of the same task terminal status is deduplicated by the
  Brain Runtime projection

Learning invariants:

```text
raw_prompt_capture = false
raw_response_capture = false
hidden_reasoning_capture = false
secret_persistence = false
self_modification = false
model_weight_update = false
automatic_skill_rewrite = false
refinement_proposals_require_review = true
```

## Phase 10 — Operational Skills and Capability Graph

### Skill contract

`SkillDefinition` is now an operational contract with:

- versioned identity
- capabilities
- Skill dependencies
- named Tool requirements
- Tool-capability requirements
- permissions
- required evidence
- procedure
- preconditions
- postconditions
- recovery guidance

Core Brain Skills contain explicit procedures. Domain Skills contain concrete
capability/dependency/tool/permission/evidence contracts and are not treated as
permission grants or Tool adapters.

### Domain Skill Packs

Contract: `brain-domain-skills-phase-10`

Installed by the default Brain Runtime:

1. `software_development`
   - repository cartography
   - code/source discovery
   - architecture inspection
   - build/test inspection
   - debug diagnosis
   - change preview
   - controlled test/build execution
   - regression verification
2. `github_ci`
   - repository status
   - CI diagnosis
   - approval-gated branch file change
   - PR evidence comment
   - exact-SHA verification
3. `research_knowledge`
   - evidence gathering
   - source comparison
   - grounded synthesis
   - known/unknown tracking
4. `documents_data`
   - document structure reading
   - table extraction
   - schema inference
   - data conflict detection
5. `google_workspace`
   - authorized Workspace reading contract
   - approval-required Workspace change planning
6. `shift_scheduling`
   - roster reading
   - shift conflict analysis
   - replacement planning
   - calendar change planning
7. `reliability_security`
   - incident diagnosis
   - recovery planning
   - permission review
   - secret boundary review

A registered Skill does **not** imply its Tool exists. System/Capability
Introspection must continue to distinguish Skill support from real adapter
readiness.

### Capability Graph

Contract: `brain-capability-graph-phase-10`

Implemented in `v2_capability_graph.py` as a dynamic projection over canonical
registries. It is never persisted as a second source of truth.

Graph relationships include:

```text
Agent -> provides -> Capability
Agent -> declares -> Permission
Skill -> provides -> Capability
Skill -> depends_on -> Skill
Skill -> requires_tool -> Tool
Skill -> requires_tool_capability -> Tool Capability
Skill -> requires -> Permission
Tool -> provides -> Tool Capability
Tool -> requires -> Permission
```

Resolution reports:

- known vs unknown capability
- ready/routable Agents
- matching Skills
- Skill dependency blockers
- named Tool availability
- Tool-capability matches
- executable Skill routes
- reasoning-only Skills that intentionally have no direct Tool execution path

The graph is used by `BrainRuntime.plan()` and is available through
`BrainRuntime.resolve_capabilities()`.

## Phase 10 — Brain Inspector UI

Flutter Agent Center now embeds a read-only `AI Brain Inspector` in
`brain_inspector_panel.dart`.

It displays:

- Brain readiness
- operational Agent and Brain Team counts
- ready Skill/Tool counts
- mutating Tool count
- capability catalog state
- representative ready Skills and Tools
- bounded read-only Brain plan preview

The inspector uses only the existing Phase 7 introspection and planning API.
It does not expose execution, permission grants, hidden chain-of-thought,
release/deploy or production controls.

## Canonical owners

Research OS keeps One Truth by reusing existing owners:

- Agent routing/readiness: `AgentRegistry`
- dependency run graph: `AgentOrchestrator`
- Brain Skills: `SkillRegistry`
- Tool metadata/adapters: `ToolRegistry`
- authorization/execution: `HardenedExecutionController`
- task bindings/evidence: `GovernedTaskStore`
- working task cognition: `WorkingMemory`
- activity/experience history: `ActivityLedger`
- project learning projection: `LearningEngine`
- provider/model inference: AI Gateway
- workspace knowledge: existing Workspace Knowledge Engine

Capability Graph and Learning patterns are projections over these owners, not
parallel canonical stores.

## Current execution boundary

The internal Brain can compose:

```text
Goal -> Plan -> Capability -> explicit Skill/action binding
     -> Agent selection -> AgentOrchestrator
     -> Skill -> Tool -> permission/approval
     -> execution -> evidence -> verification -> learning
```

It still intentionally does not expose an external Intelligence `/execute`
endpoint. That remains closed until the later connection hardening pass proves
identity, ownership, approval binding and production gateway controls.

The Brain still has no unrestricted terminal/shell, arbitrary filesystem access,
file deletion, GitHub merge/workflow dispatch/tag/release/deployment, automatic
Google Workspace writes, release promotion or production deployment bypass.

## Validation order

Per current development order, code is completed first. After the code freeze for
this Brain slice, validation is performed as one coherent pass:

```text
1. analyze
2. build
3. test
4. inspect and fix runtime/UI/provider/tool connections
5. repeat only the validation affected by any connection fix on the new exact SHA
```

A previous green SHA is not evidence for a later code SHA.

## Release boundary

- Branch: `feature/v2-ai-brain-core`
- Base: `hardening/v2-rc2-ai-gateway`
- frozen RC1 remains untouched
- Draft PR only
- no merge to `main`
- no tag or GitHub Release
- no public V2 announcement
- no V2 production deployment
