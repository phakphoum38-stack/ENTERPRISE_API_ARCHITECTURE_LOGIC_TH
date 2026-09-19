# Research OS Flutter Contract Extraction

## Objective

Extract stable contracts from the three existing Flutter roots before moving feature code. The target is one canonical user-facing Control Center while preserving multiple systems, runtimes, and platform release boundaries.

## Source contracts

| Source | Existing boundary | Canonical migration role |
|---|---|---|
| `apps/research_os_flutter` | `ResearchOSApiClient` | General Research OS capability adapter |
| `owner_special/flutter_app` | `OwnerFriendApi` | Canonical Control Center / Friend adapter |
| `v3/flutter_app` | `V3Api` | V3 compatibility adapter |

All three currently use Dart SDK `>=3.4.0 <4.0.0`. The convergence problem is therefore primarily **contract ownership and application-root duplication**, not a Dart-version collision.

## Stable contract layers

### 1. Runtime status

Normalize the minimum runtime contract around `status`, with optional `version`, `server`, `loopback_only`, and `capabilities`.

### 2. Provider

Keep provider identity and operational state behind an adapter. The UI should not know whether the provider came from the Research OS API, Owner Friend runtime, or V3 compatibility layer.

### 3. Identity

Authentication state is a capability contract. Session tokens, OAuth state, and transport headers remain adapter-owned.

### 4. Memory

Expose memory search and conversation synchronization as capabilities. Sync keys remain outside presentation widgets.

### 5. Orchestration

The UI can display and request lifecycle transitions, but authority/execution remains outside the presentation layer:

`INTENT → VALIDATE → AUTHORIZE → EXECUTE → OBSERVE → EVIDENCE → COMPLETE`

### 6. Platform

Windows, iOS, Android, Web, and future platforms are adapters/runners. A generated Flutter runner is not treated as a separate application system.

## Adapter boundary

The canonical shell should depend on capability interfaces rather than concrete HTTP implementations:

```text
Control Center
      |
      +-- RuntimeStatusCapability
      +-- ProviderCapability
      +-- IdentityCapability
      +-- MemoryCapability
      +-- ResearchCapability
      +-- GitHubCapability
      +-- OrchestrationCapability
      |
      +-- Owner Friend Adapter
      +-- Research OS API Adapter
      +-- V3 Compatibility Adapter
      |
      +-- Windows / iOS / Other platform adapters
```

This allows the existing implementations to remain intact while features are moved incrementally.

## First migration slice

1. Keep all three Flutter roots intact.
2. Define capability interfaces and normalized domain shapes.
3. Wrap existing API clients behind those interfaces.
4. Move one feature at a time into `owner_special/flutter_app`.
5. Add contract-level tests using fake adapters.
6. Keep V3 and Owner Special release gates active.
7. Retire duplicate UI roots only after feature parity, platform identity, installer, CI, and evidence gates are verified.

## Safety invariants

- No history rewrite, reset, or force push.
- No baseline alteration.
- No deletion of a Flutter root during extraction.
- No second Control Center.
- No second runtime, memory, scheduler, or assurance plane.
- No platform runner regeneration as part of UI convergence.
- No authority escalation through UI code.

The machine-readable contract is maintained in `current/RESEARCH_OS_FLUTTER_CONTRACT.json` and is intentionally descriptive at this stage; it does not grant execution or merge authority.
