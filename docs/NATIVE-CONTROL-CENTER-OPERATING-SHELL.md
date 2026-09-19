# Native Research OS Control Center — Operating Shell

The Native Control Center is the single user-facing control plane for Research OS. It is not a second runtime, scheduler, assurance engine, memory system, or authority system.

## Four engines

- **Control** — command preparation, lifecycle, modes, and bounded actions.
- **Experience** — native GUI, UX, UI, motion, accessibility, and rendering.
- **Knowledge** — context, research, learning, evidence relationships, and inspection.
- **Assurance** — provenance, verification, audit, recovery evidence, and release evidence.

## One command lifecycle

`INTENT → VALIDATE → AUTHORIZE → EXECUTE → OBSERVE → EVIDENCE → COMPLETE`

Failures enter `RECOVER`; they never become successful completion.

## Modes

- **LIVE** — actual execution through an existing authoritative runtime.
- **SIMULATION** — model the operation without live execution.
- **DRY_RUN** — validate intended work without executing it.
- **REPLAY** — inspect/reproduce an existing recorded path.

The kernel does not perform network, process, credential, GitHub, or filesystem I/O. Adapters remain responsible for those operations.

## Native UI surfaces

The Control Center can expose:

- Command Center / universal search
- Live System Map
- Universal Inspector
- Activity Stream
- Runtime/resource state
- Evidence Explorer
- Failure and recovery state
- Human Control Boundary
- Simulation / dry-run / replay selectors

## Authority boundary

Observation, evidence, confidence, or UI state never grants authority. Approval, authorization, high-risk actions, release, merge, branch-protection changes, and history mutation remain outside this kernel.

## Design principle

Every visible control should correspond to a real state, action, or evidence path. Decorative controls must not imply capabilities that the runtime does not provide.
