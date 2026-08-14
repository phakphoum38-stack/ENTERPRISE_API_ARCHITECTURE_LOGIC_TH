# Research OS — New GUI Modular Implementation Plan

Status: ACTIVE
Base branch: `integrate/research-os-3.2-unified-10x10`
Work branch: `work/research-os-new-gui-modular`

## Guard rails

- Preserve existing Flutter feature modules and backend contracts unless a verified migration is required.
- Do not replace working modules with visual-only placeholders.
- Keep mutable actions permission-scoped.
- Do not claim system health, provider readiness, or connection status without runtime evidence.
- Use Virtual Figma first; batch remote Figma writes only after local composition and audit.
- Keep AMR/6^6 bounded: logical scale must not imply uncontrolled concurrent workers.

## Current Flutter composition

The current shell already composes modules instead of placing the whole product in one file.

Existing feature destinations identified:

- Home
- AI Chat
- Agent Center
- Check-in
- Library
- Knowledge Graph
- GitHub
- Google Workspace
- Local API & Service
- System Monitor
- Settings
- Developer Access

Supporting structure:

- `lib/src/api/`
- `lib/src/features/`
- `lib/src/platform/`
- `lib/src/ui/`
- `lib/src/app_shell.dart`
- `lib/src/research_os_app.dart`

## Target information architecture

### MAIN

- Home
- Chat AI
- Agents
- Memory
- Skills
- Tools
- Factory
- Providers

### WORKSPACE

- Files
- Repositories
- GitHub
- Drive

### SYSTEM

- Runtime
- Installer
- Backup
- Restore
- Shell

## Module mapping strategy

New GUI destination | Existing module / backend source | Action
---|---|---
Home | `features/home` + health/runtime APIs | MODIFY shell presentation, KEEP backend
Chat AI | `features/chat` + `ResearchOSApiClient.answerWithMemory` | MODIFY UI, KEEP working contract until unified chat contract is verified
Agents | `features/agents` | KEEP + embed in new shell
Memory | memory/search + evidence runtime | ADD destination using existing APIs/runtime
Skills | skill registry/runtime | ADD destination, do not hard-code counts
Tools | tool registry/runtime | ADD destination, permission-aware
Factory | orchestration APIs | ADD destination on top of existing orchestration endpoints
Providers | `/v1/providers` + provider settings | ADD destination using live provider state
Files | workspace/library services | REUSE existing capabilities
Repositories | workspace/GitHub services | REUSE existing capabilities
GitHub | `features/github` | KEEP + restyle
Drive | `features/google_workspace` / Drive | KEEP + restyle
Runtime | `features/local_api` | KEEP + restyle
Installer | installer service/scripts | ADD UI adapter
Backup | backup services/scripts | ADD UI adapter
Restore | restore services/scripts | ADD UI adapter
Shell | controlled local command surface | ADD with explicit execution boundary

## Chat contract checkpoint

Current Flutter chat uses:

`ChatPage -> ResearchOSApiClient.answerWithMemory(question) -> POST /v1/ai/answer-with-memory`

The installed GUI screenshot that reported `http://127.0.0.1:8788/v3/chat` must therefore be treated as a separate/older contract until the backend and installed source are matched. The new GUI must not introduce a second incompatible request body.

## New Chat empty state

Required primary greeting:

`สวัสดีเริ่มทำอะไรดี`

Supporting copy can remain secondary and must not replace the requested greeting.

## Visual target

- Dark navy Research OS control-center shell
- Collapsible left navigation
- Conversation list adjacent to Chat AI
- Main chat workspace in the center
- Live system/agent/memory panel on the right
- Bottom tool-discovery workflow only when it reflects real execution/evidence
- Official Research OS app icon/brand mark used consistently in Flutter shell and launcher assets

## Workstreams

### A — GUI / Virtual Figma

1. Compose shell from existing Research OS design tokens.
2. Map every visible widget to a real module or status source.
3. Audit layout, density, Thai text, accessibility, and responsive states.
4. Freeze design delta before remote sync.

### B — Flutter

1. Refactor shell/navigation without deleting feature modules.
2. Add new destination adapters for Memory, Skills, Tools, Factory, Providers and System pages.
3. Restyle existing feature pages incrementally.
4. Add official launcher/app brand assets.

### C — Core / API

1. Inventory all endpoints consumed by Flutter.
2. Unify Chat contract before switching endpoints.
3. Expose real Skills/Tools/Memory/Factory/Provider status to GUI.
4. Preserve permission boundaries for write/execute operations.

### D — QA / Release

1. Add/extend widget tests for navigation and Chat empty state.
2. API contract tests.
3. End-to-end Flutter -> API -> Brain/Provider -> response evidence.
4. Installer/upgrade/uninstall regression.
5. SHA256 and rollback artifact preservation.

## Execution order

1. Freeze + inventory
2. Module/API map
3. Virtual Figma shell
4. Flutter shell/navigation
5. Chat UI + contract verification
6. Module adapters
7. Live status wiring
8. Regression tests
9. Remote Figma batch sync
10. Build + installer + evidence

## Definition of done

The GUI is not considered complete until every visible functional control is either wired to a real capability or explicitly marked unavailable, all preserved modules pass regression, Chat round-trips successfully, status cards reflect runtime evidence, and the release artifact passes install/upgrade/uninstall checks.
