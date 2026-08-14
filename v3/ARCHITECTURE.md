# Research OS V3.2 Unified Architecture

## Core rule

V3.2 has one orchestration authority. Brain, skills, tools, agents, providers, memory, factory execution, Owner/Friend compatibility code, and UI surfaces do not create competing control planes.

## Adaptive hierarchy

| Profile | Fanout | Depth | Maximum logical capacity |
|---|---:|---:|---:|
| `1^3` | 1 | 3 | 1 |
| `3^1` | 3 | 1 | 3 |
| `3^3` | 3 | 3 | 27 |
| `6^3` | 6 | 3 | 216 |
| `3^6` | 3 | 6 | 729 |
| `6^6` | 6 | 6 | 46,656 |
| `10^10` | 10 | 10 | 10,000,000,000 |

Capacity is a planning ceiling. The Brain selects the smallest profile that satisfies demand. `10^10` never means ten billion live assistants, threads, or processes; real execution stays bounded by explicit concurrency limits, queueing/backpressure, approval boundaries, provider limits, and host resources.

## Control flow

```text
Request
  -> UnifiedMasterOrchestrator
      -> Brain Core (select adaptive logical scale)
      -> Memory (retrieve local scoped context)
      -> Unified Skill Registry / NativeSkillRuntime
      -> Unified Tool Registry (risk + approval boundary)
      -> Unified Agent Registry (role execution under same master)
      -> Provider Registry (ready provider, no secret exposure)
      -> Software Factory / FactoryExecutionEngine
          -> Master -> Factory -> Team -> Tests -> Release
      -> Contracts / audit / evidence
```

## Chat compatibility

The canonical V3.2 input is `message`. The local service also accepts `text`, `prompt`, and `question` for compatibility. Responses retain `research-os-v3-chat-v1`, user/profile isolation, session/mode fields, provider metadata, memory hits, and adaptive decision metadata.

The master status keeps the legacy `unified-master-orchestrator-v3-clean` contract field for existing consumers while exposing `authority_contract=unified-master-orchestrator-v3-full` for the unified Full System authority.

## Security and execution boundaries

- The local service binds only to loopback.
- Credentials are resolved outside Flutter and are never returned in safe status payloads.
- Structured HTTP audit records timestamp, method, path, and status only.
- Mutable data is isolated by user/profile under the V3 data root.
- State-changing skill/tool paths require explicit approval where defined.
- Drive tool packages are path-contained and integrity-checked before supported runtime invocation.
- Shell execution is not implied by model output; explicit governed runtime results are required as evidence.

## Windows candidate boundary

The Windows candidate packages the Flutter app, self-contained ServiceHost, V3 Python source/runtime, and installer assets. Validation uses the installed service and installed executable, including the installed-app startup proof for `/health`, `/v3/user`, `/v3/providers`, and `/v3/chat`. Upgrade/uninstall flows preserve the governed data root while removing application/service binaries as required.
