# V3 Clean Architecture

## Core rule

V3 Clean has one authority for orchestration. Components may execute work, but they do not create competing control planes.

## Adaptive hierarchy

| Profile | Fanout | Depth | Maximum leaf capacity | Intended use |
|---|---:|---:|---:|---|
| `1^3` | 1 | 3 | 1 | tiny/single-path tasks |
| `3^3` | 3 | 3 | 27 | normal multi-step work |
| `6^3` | 6 | 3 | 216 | large parallel work |
| `6^6` | 6 | 6 | 46,656 | maximum logical capacity, allocated lazily |

Capacity is a ceiling, not a command to instantiate every assistant. The Brain Core selects the smallest profile that satisfies the workload estimate and policy constraints.

## Control flow

```text
Request
  -> Unified Master Orchestrator
      -> Brain Core (select scale)
      -> Provider Registry (select ready provider)
      -> Software Factory (derive execution plan)
          -> Factory
          -> Team
          -> Tests
          -> Release
      -> Evidence / status contracts
```

## Boundaries

- Brain Core decides scale; it does not call external providers.
- Provider adapters call model/provider APIs; they do not choose system-wide scale.
- Software Factory converts an accepted orchestration decision into stages.
- App/UI consumes contracts; it does not own core business logic.
- Windows Service owns local lifecycle/transport; it does not own orchestration policy.
- Installer packages validated outputs; it is not a source of truth.

## Provider security and resilience

- Provider credentials are never owned by the Flutter desktop client or returned by status contracts.
- The default secret source checks the process environment first and then the OS-native Windows Credential Manager using namespaced Generic Credential targets such as `ResearchOSV3/OPENAI_API_KEY`.
- Secret values are used only for provider requests and are excluded from provider status, HTTP audit logs, candidate manifests, and incremental evidence.
- Provider invocation uses a bounded retry policy with explicit request timeouts.
- Repeated provider failures open a circuit breaker; an open provider is temporarily treated as unavailable.
- The registry may fall back to another ready provider after the preferred provider exhausts retries or has an open circuit.
- Resilience status reports only safe metadata such as circuit state, failure count, and retry count.

## Local service and data ownership

- The V3 service binds only to loopback and exposes stable `/health`, `/v3/master`, and `/v3/providers` contracts.
- Mutable local data has one root: `ProgramData\\ResearchOSV3` on installed Windows systems.
- Sessions, database, artifacts, logs, and evidence are preserved across in-place upgrades and clean application uninstalls.
- Structured HTTP audit records only timestamp, method, path, and status; it excludes headers, query credentials, tokens, and secret values.

## Installer and candidate rule

- V3 has one Windows Setup EXE containing the Flutter app, self-contained ServiceHost, V3 Python core, and bundled Python runtime.
- Candidate validation uses the installed executable and installed service, not development copies.
- Required gates cover clean install, readiness, loopback binding, master/provider contracts, app-to-service E2E, in-place upgrade, data preservation, uninstall, and service/listener cleanup.
- The final candidate manifest is emitted only after every mandatory gate passes on the exact target SHA.

## Evidence rule

Each successful gate is recorded immediately. A later failure cannot erase earlier evidence. Final candidate success is derived only after all mandatory gates are successful.
