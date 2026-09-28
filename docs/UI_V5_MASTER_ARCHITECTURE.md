# Research OS UI V5 — Master Architecture

Status: DESIGN BASELINE
Canonical source inspected: `a72020dfaa512a79acb6d876c74172b433cfea4e`
Protected production/code baseline: `565ab068d5a1540ea799b594ff031ba003e068af`

## 1. Mission

UI V5 is a capability-first, Friend-centric workspace. It is not a visual recolor of the existing shell and it must not delete or silently downgrade existing capabilities.

The primary interaction is a persistent Friend conversation that can operate by voice or text and can open the correct workspace from user intent.

## 2. Non-negotiable invariants

- One Research OS product; do not split capabilities into unrelated apps.
- Preserve existing API, runtime, evidence, identity, memory, GitHub, Google Workspace, Library, Graph, Brain, Factory, Owner and Owner Special contracts.
- Preserve existing tests and add regression coverage for the V5 interaction layer.
- User level is an authority/capability model, not a cosmetic dropdown.
- Memory and Evidence remain separate concepts.
- Copilot and Codespaces are first-class Developer Workspace capabilities, not isolated chat products.
- Voice and text are modalities of the same Conversation Core.
- Owner-sensitive actions follow Intent → Evidence → Confirmation → Action → Audit.
- No V5 UI dependency on decorative image assets is required; existing branding assets remain preserved unless separately retired by an explicit source decision.
- Never modify the protected production/code baseline.

## 3. Current-to-V5 transformation

### Current shell

The current Flutter shell exposes page-indexed destinations including Home, Voice Conversation, Agent Center, Library, Knowledge Graph, GitHub, Google Workspace, Local API, System Monitor, Settings, Developer Access, Brain Skills, Google Login and Friend Connect.

### V5 shell

```text
ResearchOSAppShell
├── CapabilityRegistry
├── UserLevel / Authority
├── ConversationController
├── AdaptiveNavigation
├── FriendWorkspace
└── WorkspaceRouter
    ├── ResearchWorkspace
    ├── DeveloperWorkspace
    ├── BrainWorkspace
    ├── FactoryWorkspace
    ├── KnowledgeWorkspace
    ├── EvidenceWorkspace
    └── OwnerWorkspace
```

The existing pages are re-homed behind workspaces and capability routes rather than removed.

## 4. User levels

| Level | Primary experience | Additional capabilities |
|---|---|---|
| User | Friend, voice, text, research, memory, library | Basic workspaces and results |
| Power User | Advanced research and operations | Brain, agents, graph, automation, factory |
| Developer | Engineering workspace | GitHub, Codespaces, files, terminal, tests, build, CI/CD, Copilot |
| Owner | Governance and system control | Identity, evidence, provenance, authority, release, governance |
| Owner Special | Privileged Friend Complete experience | Runtime, deployment, release and privileged owner operations |

Inheritance is cumulative unless an explicit policy denies a capability.

## 5. Conversation Core

```text
Friend
├── Voice input
├── Text input
├── Transcript
├── Intent detection
├── Context
├── Memory
├── Copilot capability
├── Action proposal
├── Workspace routing
├── Evidence references
└── Response / speech output
```

VoiceConversation is therefore a modality surface, not a separate product destination.

## 6. Workspace information architecture

```text
FRIEND

WORK
  Research
  Develop
  Brain
  Factory

KNOWLEDGE
  Memory
  Library
  Evidence

SYSTEM
  Identity
  Owner
  Settings
```

Visible navigation is filtered by the active user level and runtime capabilities.

## 7. Research Workspace

```text
Query → Sources → Findings → Synthesis → Evidence
```

Every material result should expose its evidence path without forcing the user into a separate report application.

## 8. Developer Workspace

```text
Repository
├── Branch
├── Codespace
├── Files
├── Editor / Diff
├── Friend / Copilot context
├── Terminal
├── Tests
├── Build
├── CI
└── Pull Request
```

Canonical interaction:

```text
User request
→ Friend intent
→ context resolution
→ repository / Codespace
→ file or symbol
→ Copilot analysis
→ proposed change
→ test
→ evidence
→ explanation
```

## 9. Brain Workspace

```text
Task
├── Reasoning state
├── Agents
├── Skills
├── Orchestrator
├── Memory / Context
└── Capacity / runtime state
```

Brain is an operational workspace, not a settings screen.

## 10. Factory Workspace

```text
PLAN → GENERATE → BUILD → TEST → VERIFY → EVIDENCE → RELEASE
```

The workspace must expose stage state and evidence links without duplicating the underlying orchestration system.

## 11. Knowledge Workspace

Memory and Library provide remembered context and durable knowledge. Knowledge Graph provides relationship navigation. They are distinct capabilities but share a common Knowledge Workspace shell.

### Memory

What Friend remembers about work and context.

### Evidence

What the system can prove about source, change, test, provenance, review and authority.

These must never be visually conflated.

## 12. Evidence Workspace

```text
Source SHA
→ Root Cause
→ Source Fix
→ Tests
→ Provenance
→ Forensic
→ Independent Review
→ Authority
→ Release readiness
```

Evidence is an operational trust layer, not a static report page.

## 13. Owner Workspace

```text
System Health
Identity
Evidence
Authority
Release
Governance
Pending Decisions
```

Privileged actions require an explicit intent, supporting evidence, confirmation, action execution and audit record.

## 14. Desktop architecture

Desktop uses three conceptual regions:

```text
┌──────────────┬───────────────────────────────┬─────────────────┐
│ Adaptive Nav │ Active Workspace              │ Friend Context  │
│              │                               │                 │
│ capabilities │ task / research / dev / brain│ conversation     │
│ by authority │ / factory / evidence / owner  │ memory / action  │
└──────────────┴───────────────────────────────┴─────────────────┘
```

The Friend Context region can collapse without destroying the conversation state.

## 15. Mobile architecture

Mobile is Friend-first:

```text
Friend / Conversation
        ↓
Current Workspace
        ↓
Voice / Action
        ↓
Adaptive navigation
```

Do not compress the desktop sidebar into a narrow copy. Use task-oriented navigation and persistent conversation state.

## 16. Component architecture

Required foundational component families:

- FriendPresence
- VoiceOrb / VoiceControl
- ConversationComposer
- ConversationTranscript
- ContextStrip
- MemoryChip / MemoryPanel
- EvidenceBadge / EvidencePanel
- WorkspaceHeader
- WorkspaceSwitcher
- CapabilityRail
- TaskCard
- AgentStatus
- BrainStatus
- FactoryStageRail
- RepositoryContext
- CodespaceContext
- DiffPreview
- TestStatus
- CIStatus
- AuthorityStatus
- OwnerActionGuard
- AuditTrail
- ResponsiveNavigation

Components must remain capability-neutral where possible and receive state from domain controllers rather than duplicating business logic.

## 17. Routing model

Do not use raw integer page indexes as the long-term identity of a V5 workspace.

Preferred conceptual route identity:

```text
friend
research
developer
brain
factory
memory
library
evidence
identity
owner
settings
```

Legacy page indexes may remain as a compatibility layer during migration.

## 18. Migration sequence

### Stage A — Contract lock

Freeze feature inventory, capability inventory, user levels, existing route mapping and test expectations.

### Stage B — V5 foundation

Introduce capability registry, user-level model, workspace route model and conversation state model without removing legacy pages.

### Stage C — Friend shell

Build the Friend Workspace and persistent Conversation Core.

### Stage D — Workspace migration

Migrate existing features into Research, Developer, Brain, Factory, Knowledge, Evidence and Owner workspaces one domain at a time.

### Stage E — Responsive migration

Introduce desktop adaptive rail and mobile Friend-first navigation.

### Stage F — Regression validation

Run Flutter analysis/tests plus feature-specific tests. Verify all legacy routes remain reachable during migration.

### Stage G — Forensic / independent review

Verify that no capability, permission boundary, evidence path or contract was silently lost.

### Stage H — Merge / post-merge gate / rebaseline

Use the existing assurance protocol. UI V5 work does not bypass the repository's normal provenance and authority chain.

## 19. Definition of Done

- Feature inventory complete.
- Capability registry complete.
- User-level matrix complete.
- Permission matrix complete.
- Preservation matrix complete.
- Conversation Core implemented.
- Voice integrated as a modality.
- Text fallback preserved.
- Memory preserved.
- Cloud sync preserved.
- Copilot preserved.
- GitHub preserved.
- Codespaces preserved.
- Google Workspace preserved.
- Library preserved.
- Knowledge Graph preserved.
- Agents preserved.
- Brain Skills preserved.
- Orchestrator preserved.
- Factory preserved.
- Evidence preserved.
- Provenance preserved.
- Owner controls preserved.
- Owner Special preserved.
- Desktop responsive behavior validated.
- Mobile behavior validated.
- Existing contracts preserved.
- Existing tests preserved.
- New UI regression tests added.
- Local validation green.
- GitHub validation green.
- Forensic validation green.
- Independent review complete.
- Authority packet complete.
- Owner authority obtained before merge.
- Post-merge master gate green.
- Rebaseline recorded.
