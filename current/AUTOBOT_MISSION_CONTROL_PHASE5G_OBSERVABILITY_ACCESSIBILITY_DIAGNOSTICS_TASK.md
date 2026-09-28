# Autobot Mission Control Phase 5G — Observability, Accessibility, and Diagnostics Task

## Objective
Harden the Mission Control desktop surface for real-world use by making state, uncertainty, truncation, source health, and accessibility explicit without adding execution authority or changing canonical runtime semantics.

## Lineage
Continue from the exact Mission Control development HEAD after Phase 5F. Record exact base SHA and implementation HEAD SHA. Do not silently rebase onto a moving branch.

## Scope
Improve presentation quality and diagnostics across the existing Mission Control desktop surface while consuming only validated read-only data from the established 4H–5F contracts.

The work must preserve:
- owner/session isolation;
- `read_only=true`;
- canonical authority declarations;
- authoritative gate semantics;
- evidence/provenance semantics;
- truncation and uncertainty;
- four-user/four-EXE identity separation;
- existing Research OS shell/navigation behavior.

## Observability requirements
Expose bounded, human-readable diagnostics for:
- snapshot/source identity;
- synchronization state;
- accepted/rejected snapshot reason;
- source unavailable/unknown state;
- stale rejection;
- owner/session mismatch;
- validation failure;
- truncation indicators and affected bounded collections;
- authoritative status categories (`PASS`, `FAIL`, `PENDING`, `UNKNOWN`);
- build/release identity only when backed by canonical evidence;
- evidence/provenance availability without fabricating evidence.

Diagnostics must distinguish facts from uncertainty. Do not turn missing data into success or infer health from silence.

## Diagnostic safety
Diagnostics must never expose:
- credentials;
- API keys;
- bearer tokens;
- passwords;
- private keys;
- cookies/session secrets;
- provider response bodies;
- hidden runtime commands;
- executable descriptors;
- shell/process instructions;
- arbitrary URLs with side effects;
- internal authorization secrets.

Diagnostic messages must not contain enough dynamic content to become executable instructions.

## Accessibility
Implement accessibility support for:
- Mission Control navigation entry;
- read-only indicator;
- synchronization state;
- timeline and capability-health sections;
- evidence/provenance status;
- build/release identity status;
- gate status;
- truncation and uncertainty warnings;
- invalid/stale/source-unavailable errors.

Requirements:
- meaningful semantic labels rather than color alone;
- clear text for PASS/FAIL/PENDING/UNKNOWN;
- keyboard-accessible navigation;
- deterministic focus order;
- focus restoration after route transitions where practical;
- sufficient announcement semantics for state changes without noisy repeated announcements;
- no accessibility control may invoke execution, approval, policy mutation, or hidden refresh.

## Diagnostics model
If a structured diagnostics model is introduced, it must be:
- versioned;
- bounded;
- immutable/read-only;
- owner/session scoped;
- deterministic;
- schema validated;
- presentation-only.

Reuse existing diagnostic/state contracts when available instead of creating parallel status authorities.

## Error UX
Provide explicit, actionable-but-non-executing explanations for:
- `INVALID_SOURCE`;
- stale snapshot;
- owner mismatch;
- malformed payload;
- oversized payload;
- source unavailable;
- unknown state;
- truncated collections.

“Actionable” means explaining what state is present, not embedding commands or automatic recovery actions.

## Performance and privacy
- Diagnostics must remain bounded and cheap to render.
- Do not recursively stringify unrestricted runtime objects.
- Do not retain rejected payloads unnecessarily.
- Do not log secrets or full provider payloads.
- Do not cache diagnostics across owner/session boundaries.
- Do not create background polling merely to update diagnostics.
- Reuse the existing 5E synchronization path for read-only updates.

## Tests / evidence
Add tests for:
1. accessible Mission Control navigation;
2. explicit read-only semantics;
3. text-based status semantics independent of color;
4. deterministic keyboard/focus order;
5. state-change announcement behavior;
6. invalid/stale/owner-mismatch diagnostics;
7. truncation and uncertainty visibility;
8. malformed/oversized diagnostic payload rejection;
9. secret/token/private-key/provider-body redaction or rejection;
10. executable/dynamic diagnostic content rejection;
11. owner/session diagnostic isolation;
12. no execution/tool/MCP/Computer Use side effects;
13. no approval/policy/registration mutation;
14. bounded diagnostic rendering performance;
15. deterministic repeated rendering.

Produce:
- clean `current/AUTOBOT_MISSION_CONTROL_PHASE5G_OBSERVABILITY_ACCESSIBILITY_DIAGNOSTICS.diff`;
- machine-readable evidence with exact base/head SHA, schema/version, changed files, tests/results, diff SHA-256, bounds, owner isolation, and authority declarations;
- documentation for observability, accessibility, diagnostics, and redaction rules.

## Authority invariants
- execution → `FriendOrchestrator`
- authorization → `OwnerPolicy`
- approval → `ApprovalGate`
- trace source → `AgentRuntime`
- snapshot/presentation → established Mission Control contracts
- synchronization → Phase 5E read-only boundary
- desktop navigation → existing Research OS shell
- diagnostics/accessibility → presentation-only; never an execution or status authority

## Workflow discipline
- No manual workflow dispatch.
- No automatic merge.
- Do not weaken existing gates.
- Do not mutate protected gate configuration.

## Completion report
Report exact base SHA, exact HEAD SHA, changed files, tests/results, diff artifact + SHA-256, evidence path, schema/version, accessibility coverage, diagnostic redaction coverage, owner isolation, and confirmation that no new authority was introduced.
