# Autobot Mission Control Phase 5C — UX Safety and Interaction Task

## Objective
Harden Mission Control UX so presentation affordances communicate state without accidentally becoming action affordances.

## Requirements
- Read-only dashboard controls are visibly non-executing.
- Any future action affordance must be separated from Mission Control observation and routed through the canonical approval/execution boundaries; Phase 5C itself adds no actions.
- Disable or omit controls whose data source is PENDING, UNKNOWN, INVALID_SOURCE, stale, conflicting, or owner-mismatched.
- Never present a rendered command, shell text, callback, URL action, process name, executable path, or provider payload as an executable control.
- Provenance/source references are display metadata only.
- Keyboard/mouse/touch/focus/hover/gesture handling must not invoke execution or mutate runtime state.
- Avoid misleading success animations, auto-refresh behavior that triggers side effects, or hidden background requests.

## Accessibility / UX
Provide clear labels, bounded text, stable ordering, visible uncertainty, and accessible status semantics. Ensure error and truncation states remain understandable without color alone.

## Tests / evidence
Widget tests must verify interaction is inert, state labels are accurate, invalid sources are blocked, and no callback/command/provider execution is attached to presentation controls. Produce `.diff` and machine-readable evidence with exact lineage and authority audit.

## Workflow discipline
Do not manually dispatch workflows. Do not merge automatically.