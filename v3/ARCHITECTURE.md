# V3 Full System Architecture

## Core rule

V3 has one authority for orchestration. Components may execute work, but they do not create competing control planes.

## Adaptive hierarchy

| Profile | Fanout | Depth | Maximum logical leaf capacity | Intended use |
|---|---:|---:|---:|---|
| `3^1` | 3 | 1 | 3 | tiny/single-path work |
| `3^3` | 3 | 3 | 27 | normal multi-step work |
| `6^3` | 6 | 3 | 216 | larger parallel work |
| `3^6` | 3 | 6 | 729 | intermediate high-branch work |
| `6^6` | 6 | 6 | 46,656 | large compound work |
| `10^10` | 10 | 10 | 10,000,000,000 | maximum logical planning ceiling |

Capacity is a ceiling, not a worker count. Brain Core selects the smallest profile that satisfies normalized demand. The Factory execution engine enforces a separate hard concurrency limit; work above that active limit is queued. Demand above `10^10` stays on the `10^10` profile with explicit queue/backpressure rather than creating a larger hidden tier.

## Unified control flow

```text
User / GUI / local client
  -> loopback-only V3 Service
      -> Unified Master Orchestrator
          -> Brain Core (select smallest safe scale)
          -> Unified Skill Registry
          -> Unified Tool Registry (risk + approval policy)
          -> Unified Agent Registry (lazy role activation)
          -> Provider Registry (ready provider + resilience)
          -> Memory Store (explicit user/profile-scoped context)
          -> Software Factory
              -> Master
              -> Factory
              -> Team
              -> Tests
              -> Release
          -> Evidence / status contracts
```

## Full System workspaces

The Flutter application consumes V3 contracts only and provides eight primary workspaces:

1. Home — service, active scale, maximum scale/capacity, capability counts.
2. Chat — provider-backed chat with local Memory and optional Agent execution.
3. Agents — on-demand governed role execution.
4. Memory — explicit durable memory add/search.
5. Skills — native V3 capability catalog with V1/V2/V3 provenance.
6. Tools — governed tools with risk metadata and explicit one-time approval for writes.
7. Factory — adaptive plan inspection and Master -> Factory -> Team -> Tests -> Release stages.
8. Providers — secret-safe readiness and connection metadata.

## Boundaries

- Brain Core decides scale; it does not call external providers.
- Provider adapters call model/provider APIs; they do not choose system-wide scale.
- Skills describe capability and provenance; they do not bypass policy.
- Tools execute only registered handlers and write-capable tools require approval.
- Agents are role definitions activated for a request; `10^10` never means permanently running billions of agents.
- Memory is explicit, user/profile isolated, and never self-modifies application code.
- Software Factory converts an accepted orchestration decision into deterministic stages.
- App/UI consumes contracts; it never owns provider credentials or core business policy.
- Windows Service owns local lifecycle/transport; it does not own orchestration policy.
- Installer packages validated outputs; it is not a source of truth.

## Provider security and resilience

- Provider credentials are never owned by the Flutter desktop client or returned by status contracts.
- Installed service discovery supports existing `RESEARCH_OS_OPENAI_API_KEY` and `OPENAI_API_KEY` references through environment / OS-native credential sources.
- `RESEARCH_OS_OPENAI_ENDPOINT` and `RESEARCH_OS_OPENAI_MODEL` can configure an OpenAI-compatible endpoint/model.
- OpenAI-compatible execution is preferred when ready; mock remains a deterministic offline fallback.
- Secret values are excluded from provider status, HTTP audit logs, candidate manifests, and incremental evidence.
- Provider invocation uses bounded retry and explicit request timeouts.
- Repeated failures open a circuit breaker; an open provider is temporarily unavailable.
- Registry fallback may select another ready provider after retries are exhausted.

## Local service and data ownership

- V3 binds only to loopback.
- Read endpoints: `/health`, `/v3/master`, `/v3/factory/plan`, `/v3/providers`, `/v3/skills`, `/v3/tools`, `/v3/agents`, `/v3/user`, `/v3/memory`.
- Governed execution endpoints: `/v3/chat`, `/v3/memory`, `/v3/agents/run`, `/v3/tools/execute`.
- Mutable local data has one installed Windows root: `ProgramData\\ResearchOSV3`.
- User/profile data is isolated under `users/<user>/profiles/<profile>/...`.
- Sessions, database, artifacts, logs, and evidence survive in-place upgrades and application uninstall according to data ownership policy.
- Structured HTTP audit records only timestamp, method, path, and status; headers, query values, tokens, and secret values are excluded.

## Approval model

Read-only tools may execute without an approval token. A tool marked `approval_required` fails closed unless the request carries `X-Research-OS-Approval: granted`. Approval is per request and does not disable the global policy for later requests.

## Installer and candidate rule

- One Windows Setup EXE contains the Flutter app, self-contained ServiceHost, V3 Python core, and bundled Python runtime.
- Candidate validation uses the installed executable and installed service, never development copies.
- Gates cover clean install, readiness, loopback binding, 10^10 contract proof, Skills/Tools/Agents catalogs, credential redaction, user isolation, installed Flutter -> Service full startup contracts, in-place upgrade, data preservation, uninstall, and service/listener cleanup.
- Final candidate success is emitted only after all mandatory gates pass on the exact target SHA.

## Evidence rule

Each successful gate is recorded immediately. A later failure cannot erase earlier evidence. Final candidate success is derived only after every mandatory gate is successful.
