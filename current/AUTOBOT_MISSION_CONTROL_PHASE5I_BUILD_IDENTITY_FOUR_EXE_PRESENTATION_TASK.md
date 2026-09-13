# Autobot Mission Control Phase 5I — Build Identity / Four-EXE Presentation Integration Task

## Objective
Integrate canonical Build Identity and Installed Owner Release Provenance into the Mission Control desktop presentation for the four-user / four-EXE architecture, without creating any build, release, installation, authorization, or execution authority inside Mission Control.

## Core principle
Mission Control **observes identity; it never creates identity**.

The authoritative chain remains:
- Build Identity Gate → authoritative build identity evidence
- Installed Owner Release Provenance Gate → authoritative installed release provenance evidence
- OwnerPolicy → authorization authority
- ApprovalGate → approval authority
- FriendOrchestrator → execution authority
- Mission Control → read-only presentation only

## Four-user / four-EXE contract
The presentation must preserve strict separation between the four intended user identities and their corresponding EXE identities.

For every displayed identity record:
- owner ID must be explicit;
- EXE/application identity must come from canonical evidence;
- build commit SHA must come from canonical evidence;
- release/install provenance must come from canonical evidence;
- missing, conflicting, stale, malformed, or unknown identity evidence must not be guessed;
- an identity belonging to another owner must fail closed;
- Mission Control must never select, switch, launch, install, uninstall, or repair an EXE.

## Canonical evidence only
Reuse existing Build Identity Gate and Installed Owner Release Provenance Gate outputs.

Do not infer identity from:
- filename alone;
- executable path alone;
- window title alone;
- display name alone;
- timestamps alone;
- package filename alone;
- directory layout alone;
- cached UI state alone.

If canonical evidence is unavailable or contradictory, expose an explicit `UNKNOWN`, `FAILED`, `INVALID_SOURCE`, or equivalent existing state rather than manufacturing a value.

## Presentation contract
Consume the validated Mission Control path:
`4H Unified Snapshot → 4I UI Projection → 5A Desktop Surface → 5B States → 5E Refresh Sync → 5F Navigation → 5G Diagnostics → 5H E2E Contract → 5I Build Identity Presentation`

Display, where authoritative evidence exists:
- owner identity;
- EXE/application identity;
- build identity;
- source commit SHA;
- release identity;
- installed provenance;
- provenance verification state;
- stale/conflict/unknown indicators;
- read-only indicator.

All displayed fields must remain bounded, immutable from the UI perspective, deterministic, and owner-scoped.

## Safety requirements
Mission Control must not:
- build or rebuild an EXE;
- package an EXE;
- sign an EXE;
- install or uninstall software;
- launch another owner's EXE;
- switch owner context to access another EXE;
- mutate Build Identity Gate configuration;
- mutate Installed Owner Release Provenance Gate configuration;
- execute PowerShell/cmd/shell/process instructions;
- invoke tools, MCP, browser, Computer Use, or Windows input;
- access credentials, API keys, bearer tokens, passwords, private keys, signing secrets, or provider response bodies;
- create a second release/provenance authority;
- silently downgrade an identity failure to PASS.

## UI state semantics
Identity presentation must distinguish at least:
- `VERIFIED` — canonical identity evidence is complete and consistent;
- `PENDING` — expected authoritative evidence is not yet complete;
- `STALE` — evidence is present but no longer valid for the required source state;
- `CONFLICT` — authoritative sources disagree;
- `UNKNOWN` — identity cannot be established;
- `INVALID_SOURCE` — source failed schema/contract validation;
- `OWNER_MISMATCH` — identity evidence belongs to another owner.

Do not collapse these states into a generic green/red indicator.

## Refresh and navigation
Identity data must follow 5E read-only synchronization semantics.

Refresh may:
- request a new authoritative read-only snapshot;
- accept a validated replacement;
- preserve unchanged validated data.

Refresh may not:
- rebuild identity;
- trigger release workflows;
- install software;
- execute tools;
- repair provenance.

Navigation must preserve owner/session isolation. Returning to Mission Control must not silently substitute another owner's identity evidence.

## Flutter integration
Integrate into the existing `owner_special/flutter_app` Mission Control surface rather than creating a second desktop shell.

Use stable widgets and keys. Identity sections must remain accessible and understandable without relying on color alone.

The UI should make it obvious that the displayed identity is **observed evidence**, not an action target.

## Tests
Add focused tests for:
1. verified Owner A identity;
2. verified Owner B/C/D identities;
3. owner mismatch;
4. missing Build Identity evidence;
5. missing Installed Provenance evidence;
6. stale identity;
7. conflicting identity sources;
8. malformed evidence;
9. oversized identity payload;
10. deterministic rendering/order;
11. refresh with unchanged identity;
12. refresh with validated identity replacement;
13. navigation preserving owner identity;
14. attempted cross-owner identity substitution;
15. attempted executable/action descriptor injection;
16. secret-like field rejection;
17. no execution/build/install side effects;
18. existing Research OS workspace/chat surfaces remain unaffected.

## Evidence artifacts
Produce:
- clean `current/AUTOBOT_MISSION_CONTROL_PHASE5I_BUILD_IDENTITY_FOUR_EXE_PRESENTATION.diff`;
- machine-readable evidence containing exact base/head SHA, schema/contract versions, owner/EXE identity test matrix, source evidence identifiers, bounds, test paths/results, and authority declarations;
- explicit side-effect audit;
- documentation describing identity provenance and four-EXE separation.

The `.diff` must not include itself and must represent only the 5I implementation change.

## Authority invariants
There is still exactly one authority for each concern:
- execution → `FriendOrchestrator`
- authorization → `OwnerPolicy`
- approval → `ApprovalGate`
- build identity → existing Build Identity Gate
- installed release provenance → existing Installed Owner Release Provenance Gate
- trace → `AgentRuntime`
- Mission Control snapshot → existing 4H contract
- presentation → existing 4I contract
- refresh/sync → existing 5E contract
- E2E verification → tests/evidence only.

## Workflow discipline
- No manual workflow dispatch.
- No merge.
- Do not weaken or bypass release/build/provenance gates.
- Do not mutate protected workflow configuration.

## Completion report
Report exact base SHA, implementation HEAD SHA, changed files, tests/results, four-owner identity matrix, evidence source identifiers, diff SHA-256, evidence path, schema/contract versions, side-effect audit, and PR URL.
