# Architecture Runtime Binding Gate

This is the second layer after ARCHITECTURE_COMPLETENESS_CONTRACT.json.

The completeness inspector answers whether the declared architecture is present. This inspector answers whether repository evidence shows that the three Flutter roots bind to the declared architecture.

Status meanings:
- PASS: concrete repository evidence satisfies the inspected rule.
- PARTIAL: evidence exists but multiple or incomplete bindings remain.
- UNPROVEN: sufficient executable or static evidence is absent.
- DUPLICATED: competing owner or binding is detected.

UNPROVEN and DUPLICATED fail closed. PARTIAL is reported separately and is never silently promoted to PASS.

The inspector is read-only. It does not edit source, history, workflows, merge state, or authority.

Command:
python tools/inspect_architecture_runtime_binding.py

JSON:
python tools/inspect_architecture_runtime_binding.py --json-out architecture-runtime-binding.json
