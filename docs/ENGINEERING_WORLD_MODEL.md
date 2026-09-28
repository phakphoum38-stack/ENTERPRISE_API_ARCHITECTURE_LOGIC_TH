# Engineering World Model & Lifecycle Graph

P0-02 establishes the canonical machine-readable graph for the engineering lifecycle.

## Canonical chain

`Requirement → Decision → Architecture → Contract → Code → Commit → Build → Artifact → Test → Evidence → Gate → Release → Installation → Runtime → Incident → Root Cause → Knowledge`

The schema is stored in `current/ENGINEERING_WORLD_MODEL_SCHEMA.json`; the end-to-end fixture is `current/ENGINEERING_WORLD_MODEL_FIXTURE.json`.

## Identity and time

Every entity and relationship has a stable `id`. `valid_from` records when the fact becomes effective. `created_at` records entity creation. History is append-only: later facts supersede earlier facts rather than rewriting them.

## Lineage and impact

Backward impact starts from an artifact/runtime and follows relationships toward its originating requirement. Forward impact follows the chain toward installation, runtime evidence, incidents and learned knowledge. Query implementations can traverse the same directed relationship set to answer “why does this exist?” and “what could this change affect?”.

## Validation boundary

`tools/validate_engineering_world_model.py` fails closed on duplicate IDs, undeclared types/states/relationship types, missing endpoints, missing required fields, and invalid timestamps. Regression tests exercise the valid fixture and representative failures.

## Handoff

P0-02 is the evidence boundary for P0-03: Engineering Constitution, Governance & Amendment Protocol. Governance rules should reference these declared entities, relationships and lifecycle states rather than inventing parallel identity or lineage models.
