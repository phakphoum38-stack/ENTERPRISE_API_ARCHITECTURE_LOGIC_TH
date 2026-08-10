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

## Evidence rule

Each successful gate is recorded immediately. A later failure cannot erase earlier evidence. Final candidate success is derived only after all mandatory gates are successful.
