# Research OS — Mission Control Phase 4C

## Purpose

Project the existing `UnifiedToolCatalog`, `ToolHealthMatrix`, and
`ToolHealthGate` into a bounded, read-only Mission Control capability panel
contract.

## Existing authorities

The implementation deliberately reuses existing runtime health surfaces.
`UnifiedToolCatalog` is already the read-only catalog over Friend, V3, and
repair tool surfaces, while `ToolHealthMatrix` already derives aggregate
health from that catalog. fileciteturn117file0 fileciteturn116file0

Mission Control adds no registration, execution, authorization, or approval
behavior.

## Contract

`MissionControlCapabilities.snapshot(limit=25)` returns:

- stable schema identifier
- owner identity
- `read_only=true`
- existing execution/authorization/approval authority declarations
- catalog health counts
- existing readiness gate snapshot
- deterministically name-sorted rows
- explicit payload limit and truncation flag

The projection is bounded to a maximum of 100 rows.

## Safety boundary

This panel is observational only. It does not:

- execute a tool
- register or unregister a tool
- alter `OwnerPolicy`
- grant or revoke approval
- change `ToolHealthGate`
- mutate the unified catalog
- invoke MCP or Computer Use

The source catalog already models readiness, external dependencies, and
connection requirements as data; the panel presents that data without changing
those states. fileciteturn117file0

## Next increment

The next presentation increment can bind this contract into the desktop shell
without introducing a second execution authority. UI rendering should consume
this schema and remain unable to invoke catalog or health mutations directly.
