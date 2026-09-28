# Autobot Mission Control Phase 5H — UI / Snapshot End-to-End Contract Task

## Objective
Prove the complete read-only Mission Control data path from authoritative runtime projection to the real Owner Special Research OS Flutter surface, without introducing a second execution, authorization, approval, routing, or data authority.

## Contract path
`AgentRuntime → 4A Trace → 4B Timeline → 4C Capability Health → 4D UI Schema → 4H Unified Snapshot → 4I UI Projection → 5A Desktop Surface → 5B State Model → 5C UX Safety → 5D Performance → 5E Refresh Sync → 5F Navigation → 5G Diagnostics → 5H E2E Contract`

## Scope
Create an integration/e2e contract that verifies the same validated snapshot semantics survive every boundary until rendered by the actual Owner Special Research OS desktop shell.

The test must verify:
- exact owner/session identity is preserved;
- `read_only=true` is preserved;
- authority declarations remain exact;
- trace/timeline/capability/evidence/build/gate sections remain bounded;
- truncation and uncertainty survive unchanged;
- synchronization state survives refresh and navigation;
- invalid, stale, malformed, oversized, conflicting, and owner-mismatched sources fail closed;
- Mission Control never reconstructs runtime state from UI assumptions;
- UI state is derived from validated source metadata only;
- navigation/restoration does not cross owner/session boundaries;
- no duplicate runtime/authority instances are created.

## E2E boundary rules
The test harness may use deterministic fixtures/fakes for authoritative read-only sources, but those fixtures must model existing contracts rather than create alternate production authorities.

Do not:
- execute real external tools, MCP, browser, Computer Use, shell/process commands, Windows input, or network side effects;
- invoke approval or policy mutation;
- fabricate release/build identity;
- treat fixture data as authoritative production evidence;
- bypass Phase 4D validation;
- bypass Phase 5E synchronization semantics;
- add a test-only execution path that can be used by production UI.

## Contract scenarios
Cover at minimum:
1. complete READY snapshot renders correctly;
2. EMPTY state renders without runtime execution;
3. LOADING/REQUESTING synchronization state is explicit;
4. UPDATED snapshot replaces the previous immutable snapshot;
5. UNCHANGED snapshot does not cause unnecessary rebuilds;
6. TRUNCATED snapshot preserves visible truncation indicators;
7. PENDING state remains pending;
8. FAILED state remains failed;
9. UNKNOWN state remains unknown;
10. INVALID_SOURCE is visible and fail-closed;
11. stale snapshot is rejected;
12. owner mismatch is rejected;
13. malformed route/source payload is rejected;
14. oversized payload is rejected;
15. conflicting source metadata is rejected;
16. back/forward navigation preserves the same owner/session;
17. workspace/chat state survives Mission Control navigation;
18. restoration after rebuild preserves validated state only;
19. refresh never triggers execution/tool/MCP/Computer Use side effects;
20. diagnostics never expose secret-like fields;
21. repeated render/refresh/navigation remains deterministic.

## Golden contract
Create compact deterministic fixtures or golden representations for the accepted presentation model. Goldens must:
- contain no secrets or provider response bodies;
- be bounded;
- use stable ordering;
- include explicit schema/version identifiers;
- include owner/read-only/authority metadata;
- make truncation and uncertainty visible;
- avoid executable/dynamic values.

Do not snapshot unstable timestamps or environment-dependent values unless they are normalized or supplied by an authoritative deterministic fixture.

## Flutter integration
Run the contract against the actual Mission Control widget tree in `owner_special/flutter_app` where feasible.

Verify:
- navigation entry exists;
- widgets consume the projection model rather than runtime internals;
- state labels are accessible;
- stable keys/order are preserved;
- bounded large datasets do not cause unbounded widget creation;
- no hidden timers/listeners survive navigation;
- unrelated Research OS surfaces remain functional.

## Evidence
Produce:
- clean `current/AUTOBOT_MISSION_CONTROL_PHASE5H_UI_SNAPSHOT_E2E_CONTRACT.diff`;
- machine-readable evidence with exact base/head SHA, contract/schema versions, fixture/golden identifiers, test paths/results, bounds, owner isolation checks, and authority declarations;
- documentation of the complete read-only contract path;
- explicit side-effect audit confirming no execution/tool/MCP/Computer Use/network/OS-input actions occurred.

## Authority invariants
- execution → `FriendOrchestrator`
- authorization → `OwnerPolicy`
- approval → `ApprovalGate`
- trace → `AgentRuntime`
- Mission Control snapshot → 4H contract
- presentation → 4I contract
- refresh/sync → 5E read-only contract
- navigation → existing Research OS shell
- E2E verification → test/evidence layer only; it is not an authority.

## Workflow discipline
- No manual workflow dispatch.
- No automatic merge.
- Do not weaken release gates.
- Do not mutate protected gate configuration.

## Completion report
Report exact base SHA, implementation HEAD SHA, changed files, tests/results, fixture/golden identifiers, diff artifact + SHA-256, evidence path, schema/contract versions, side-effect audit, owner isolation result, and PR URL.
