# Native Research OS Control Plane

This layer turns the Research OS architecture into one native control environment.

## Four engines

1. **Control Engine** — command lifecycle, navigation, bounded dispatch and human-control boundaries.
2. **Experience Engine** — native views, state transitions and reduced-motion semantics.
3. **Knowledge Engine** — knowledge objects, state promotion and evidence references.
4. **Assurance Engine** — evidence identity, provenance references and verification state.

They compose through `ResearchOSControlPlane`; they do not create a second scheduler, queue, memory system, assurance system or merge authority.

## Runtime direction

The first vertical slice is intentionally small:

`Native GUI → Control Plane → Runtime action → Observation → Evidence → GUI state`

The GUI can later use the same command and inspection models from desktop, CLI, API or Friend without changing the underlying authority model.

## Universal Inspector

`inspect(object_id)` provides one bounded inspection shape for knowledge and related evidence. The intended native UI can use the same inspector for tasks, research objects, tools, services, evidence, failures and design objects as adapters are connected.

## Motion

Motion is state-driven. Reduced motion is a first-class capability, and decorative animation must never alter system meaning.

## Human control

The system can observe, analyze, research, prepare and propose. Approval, authorization, release and high-risk override remain explicit human-controlled boundaries.

## Validation

Run:

`python tools/validate_native_control_plane.py`

Then run the focused test:

`python -m unittest owner_special.tests.test_native_control_plane`

## Boundaries

- 10^1000 remains logical coverage only.
- No automatic merge or authority grant.
- Existing history is preserved.
- Existing canonical contracts remain authoritative in their domains.
