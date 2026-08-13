# Research OS V3 Architecture

## Purpose

V3 is the clean local-first Research OS architecture. It keeps one coordination authority and separates planning capacity from actual runtime concurrency.

## One Truth

`UnifiedMasterOrchestrator` is the only V3 coordination and execution authority. Brain, Providers, Skills, Tools, Agents, Memory, and Factory compose under this master. Preserved V1/V2, Owner/Friend, House Command, Research Curator, and other legacy capabilities must not be started as competing masters.

## Adaptive hierarchy

Logical profiles are selected lazily from the smallest safe tier:

- `3^1`
- `3^3`
- `6^3`
- `3^6`
- `6^6`
- `10^10`

The `10^10` profile is a logical planning ceiling of 10,000,000,000 leaf slots. It does not create ten billion workers. Real execution is bounded by explicit concurrency limits and queue/backpressure.

## Brain and AI conversation

The AI conversation flow is:

`Flutter Chat -> loopback POST /v3/chat -> V3 Local Service -> Unified Master -> Provider Registry -> provider response`

Optional user/profile memory is resolved before the master calls the provider. The master injects the unified secret-free skill catalog as context. Provider secrets remain service-owned and are never returned in API status or stored in Flutter.

The desktop Flutter shell that historically used the V1/Gemini generation endpoints now routes Chat through `/v3/chat`. Non-chat V1/V2 compatibility APIs may remain while migration continues, but they are not independent Chat brains.

## Unified skills

`UnifiedSkillRegistry` contains the capability catalog across V1, V2, V3, Owner/Friend, and preserved legacy sources.

Each skill records:

- `origin`
- `capability`
- `description`
- `native_v3`
- `runtime_mode`
- `source`

`runtime_mode: native` means the capability has a V3-native executable implementation. `runtime_mode: context-adapter` means the capability is preserved for reasoning/routing context and must not be represented as executed unless an explicit V3 runtime, agent, or tool invocation proves execution. The metadata enforces `native_v3 = false` for context adapters.

Owner/Friend capability names preserved in the registry include analysis, planning, coding, research, data, documents, automation, memory, security, and quality. Legacy catalog entries include Research Curator, House Command, integration, developer identity, quality gates, evidence, and the preserved V3 bridge.

## Agents

The default on-demand V3 roles remain:

- researcher
- architect
- builder
- reviewer
- release-guardian

Agents are capability-validated against the unified skill/tool registries. Role prompts receive only their assigned skill context, and context-adapter skills do not grant implicit execution authority.

## Governed tools

Tool execution flows through `UnifiedToolRegistry`. Write-capable operations fail closed without explicit approval. Tool results, not model claims, are the evidence that an action ran.

## Memory and user isolation

Durable memory is scoped by user and profile. User/profile identifiers travel through V3 request headers, and storage layout keeps mutable data isolated. Cross-user memory leakage is prohibited and covered by tests.

## Provider boundary

Provider routing is service-side. OpenAI-compatible credentials can be resolved from configured secret sources; deterministic mock remains available for offline tests. Status contracts are credential-redacted.

## Validation boundary

A change is not release-ready merely because source exists. Python tests, service smoke, Flutter tests, platform build checks, and Windows Candidate validation should be run against the exact final SHA before a PR is marked Ready or merged.
