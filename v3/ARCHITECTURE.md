# Research OS V3 Architecture

## One Truth

`UnifiedMasterOrchestrator` is the only V3 coordination and execution authority. Brain, Providers, Skills, Tools, Agents, Memory, and Factory compose under this master. Restored Owner/Friend and legacy source never starts a competing master.

## Capacity

The hierarchy selects the smallest safe logical tier from `3^1`, `3^3`, `6^3`, `3^6`, `6^6`, and `10^10`. The top tier is a logical ceiling of 10,000,000,000 leaf slots. Actual execution remains bounded and queued above active capacity.

## Skills

`UnifiedSkillRegistry` contains 40 capabilities across V1, V2, V3, Owner/Friend, and legacy origins. All current entries have a native V3 execution path.

- `v3-core` identifies existing V3 implementations.
- `v3-adapter` identifies migrated implementations hosted by `NativeSkillRuntime`.
- `POST /v3/skills/execute` supplies explicit runtime evidence.
- Persisting or mutating actions fail closed without request approval.

The restored `owner_special/research_os_friend/` package is kept as provenance and compatibility source. V3 does not activate `FriendOrchestrator`.

## Tools and Drive

`UnifiedToolRegistry` applies risk and approval policy to tool execution. `DriveToolRuntimeAdapter` reads packages from a locally synchronized Google Drive root; Drive itself is not treated as a process host.

The adapter checks package path containment and SHA-256 integrity, invokes supported runtimes without a shell, and bounds execution. `drive-tools-list` is read-only; `drive-tool-execute` requires approval.

## Agents and conversation

Researcher, architect, builder, reviewer, and release-guardian remain on-demand roles under the Unified Master. Flutter Chat routes through the loopback V3 chat endpoint and does not create an independent AI brain.

## Data boundary

Memory and mutable state remain scoped by user/profile. Cross-user access is prohibited. Execution evidence and API status remain separate from provider-owned configuration.

## Validation boundary

Local Python validation for this source set passed with 120 tests, 1 platform-specific skip, and 7 subtests. Service Smoke confirms 40 native skills, 0 context-only adapters, 5 tools, 5 agents, Drive runtime availability, user isolation, and the `10^10` ceiling.

The Draft PR is not release-ready until Flutter and Windows Candidate validation run on the exact final GitHub SHA.
