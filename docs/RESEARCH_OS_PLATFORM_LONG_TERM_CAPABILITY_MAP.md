# Research OS Platform Long-Term Capability Map

This map records where the long-term Platform plan is implemented today. It is a
navigation map, not a second authority.

| Capability | Canonical implementation | State |
|---|---|---|
| Platform Constitution | `docs/RESEARCH_OS_CONSTITUTION.md` + `current/ARCHITECTURE_INVARIANTS.md` | ACTIVE |
| System Spine / Registry | `current/RESEARCH_OS_PLATFORM_GOVERNANCE_CONTRACT.json`, `current/RESEARCH_OS_PLATFORM_COMPONENT_INVENTORY.json`, `current/RESEARCH_OS_PLATFORM_COMPONENT_REGISTRY_SCHEMA.json`, `current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json` | ACTIVE |
| Architecture DNA | `current/ARCHITECTURE_INVARIANTS.md` + governance change-impact rules | ACTIVE |
| Canonical Path Registry | `current/PLATFORM_VIRTUAL_WORKSPACE_REGISTRY.json` + project registry | ACTIVE |
| Recon / Discovery | existing RECON tooling + `tools/platform_self_reconciliation.py` | ACTIVE |
| Failure Localization | `owner_special/research_os_friend/recon_failure.py`, `recon_forensics.py` | ACTIVE |
| Repair Engine | `tools/repair_diff_pipeline.py` and bounded self-reconciliation repair planning | ACTIVE |
| Sandbox / Snapshot / Rollback | `current/PLATFORM_PROJECT_SNAPSHOT_CONTRACT.json` + existing repair/continuity controls | ACTIVE |
| Blast Radius | `tools/platform_change_impact.py` + existing AEOS blast-radius tooling | ACTIVE |
| Contract Evolution | existing Platform contract/versioning sources + component compatibility metadata | ACTIVE |
| Runtime Spine | Event → Queue → Stateless Runner, universal runner and continuity contracts | ACTIVE |
| Tool Platform | existing tool/capability governance and evidence controls | ACTIVE |
| AI Integration | existing AI provider connection and orchestration boundaries | ACTIVE |
| Drift Detection | canonical-source scan + schema-driven component registry reconciliation in `tools/platform_self_reconciliation.py` | ACTIVE |
| System Knowledge | Memory Fabric + Research Curator + continuity knowledge | ACTIVE |
| Continuous Reconciliation | `.github/workflows/recon-continuous-reconciliation.yml` + self-reconciliation validator | ACTIVE |
| Control Plane | Native Control Center / Platform operating contracts | ACTIVE |
| Assurance | AEOS + platform validators + evidence lineage | ACTIVE |
| Unified Final Gate | `current/RESEARCH_OS_UNIFIED_FINAL_GATE.yml` | SINGLE RELEASE AUTHORITY |

## Non-duplication rule

Where an existing canonical capability already satisfies a planned responsibility,
the Platform composes that capability instead of creating another registry,
runtime, queue, authorization authority, evidence ledger, control plane, or release
authority.

## Self-healing boundary

Only deterministic, uniquely resolvable structural defects are eligible for
automatic repair. Protected security, authority, evidence, audit and release
boundaries remain fail-closed.


## Dynamic component evolution

The component registry is schema-driven. Component count is informational only; required components are explicit metadata. Optional extensions, lifecycle transitions, capabilities, authority metadata, dependency references, and compatibility metadata are validated without hard-coding the component list into validator code.
