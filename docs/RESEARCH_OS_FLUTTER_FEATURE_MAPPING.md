# Research OS — Flutter Feature Mapping

## Classification

- **canonical** — already belongs in the Control Center shell.
- **migrate** — capability should move into the canonical shell through an explicit contract.
- **adapter** — platform/runtime integration; keep behind an interface.
- **platform-only** — platform runner, packaging, identity, or native integration; do not merge into UI logic.
- **retire** — only after parity and all release/CI gates are proven.

## `owner_special/flutter_app`

| Area | Classification | Disposition |
|---|---|---|
| `friend_app_shell.dart` | canonical | Keep as the current Control Center shell/navigation boundary. |
| `friend_app.dart` | canonical | Keep as application composition root; reduce feature coupling over time. |
| `native_core_workspace_page.dart` | canonical | Keep as Native Core workspace inside Control Center. |
| `mission_control_desktop_page.dart` | canonical | Keep as Mission Control capability. |
| `launch_desk_page.dart` | canonical | Keep as Launch Desk capability. |
| Friend chat / Friend UI | canonical | Keep Friend as a first-class Control Center module. |
| GitHub Workbench | migrate | Reconcile into the canonical shell; preserve its contract tests. |
| Google Identity | migrate | Preserve identity boundary; UI consumes the identity contract. |
| Memory / Provider / Team / Capabilities | migrate | Keep as modules behind stable navigation/service contracts. |
| `owner_api.dart` | adapter | Keep API access behind a service contract; do not expose transport details to pages. |
| `windows/` | platform-only | Preserve Owner executable identity and canonical Windows runner. |
| installer / ServiceHost integration | platform-only | Preserve Owner installer and runtime lifecycle gates. |

## `apps/research_os_flutter`

| Area | Classification | Disposition |
|---|---|---|
| `src/app_shell.dart` | migrate | Extract reusable navigation/shell behavior where it adds capability without creating a second shell. |
| `src/research_os_app.dart` | migrate | Extract application capabilities into Control Center modules. |
| `features/chat` | migrate | Map into Friend/chat contract; avoid duplicate chat runtime. |
| `features/friend` | migrate | Reconcile with Owner Friend UI/runtime contracts. |
| `features/github` | migrate | Reconcile with canonical GitHub Workbench. |
| `features/agents` | migrate | Map to canonical agent/capability surface. |
| `features/brain_skills` | migrate | Map to Brain/Skills capability contract. |
| `features/auth` | migrate | Preserve identity/auth boundaries. |
| `features/google_workspace` | migrate | Preserve Google Workspace service boundary. |
| `features/checkin` | migrate | Preserve local-first check-in history capability. |
| `features/developer_access` | migrate | Keep behind explicit authority/access boundary. |
| `features/graph` | migrate | Map to Research/Graph capability. |
| `features/home` | migrate | Home capability becomes Control Center entry surface where applicable. |
| `features/library` | migrate | Map to Research/Library capability. |
| `features/local_api` | adapter | Preserve local-first API integration behind platform/service abstraction. |
| `features/monitor` | migrate | Map to runtime/monitoring workspace. |
| `features/settings` | migrate | Map to canonical settings surface. |
| `ui/enterprise_*`, sidebar | migrate | Reuse components/navigation patterns selectively; do not create a second shell. |
| `platform/local_api_manager*` | adapter/platform-only | Preserve platform-specific implementation behind an interface. |
| `ios/`, `windows/` runners | platform-only | Preserve platform identity and release contracts. |

## `v3/flutter_app`

| Area | Classification | Disposition |
|---|---|---|
| `research_os_v3_app.dart` | migrate | Extract V3 user-facing capabilities into the canonical shell. |
| `api/` | adapter | Reconcile with shared API/runtime contracts rather than duplicating transport logic. |
| `startup_probe.dart` | adapter | Preserve startup/runtime probe semantics behind the canonical startup contract. |
| `windows/` | platform-only | Preserve while V3 release gates depend on this root. |
| V3-specific screens/behavior | migrate | Feature-map individually before retirement. |
| V3-specific tests | migrate/compatibility | Move or establish equivalent coverage before retiring the root. |

## Current decision

`owner_special/flutter_app` is the **current shell host**, not because the other applications are obsolete, but because it already contains the integrated Control Center, Mission Control, Friend, Launch Desk, Native Core, and Owner runtime boundary.

`apps/research_os_flutter` contributes the broad cross-platform Research OS feature set and platform integrations.

`v3/flutter_app` contributes V3-specific behavior and release contracts.

Therefore the migration direction is:

```text
apps/research_os_flutter  ─┐
                           ├──> contracts/adapters ──> Owner Control Center shell
v3/flutter_app            ─┘
                                      │
                                      ├── Windows / iOS / other platform adapters
                                      ├── Friend / API / Runtime
                                      └── Evidence / Identity / Governance
```

## Retirement condition

No Flutter root is marked `retire` yet. Retirement becomes eligible only after feature parity, tests, platform identity, release/installer coverage, V3 gate migration, CI reference removal, and evidence lineage verification are all complete.

## Important finding

The three projects already share the same Dart SDK range (`>=3.4.0 <4.0.0`). The remaining problem is therefore not a Dart-version collision; it is ownership of UI capabilities, platform runners, runtime adapters, and release contracts.