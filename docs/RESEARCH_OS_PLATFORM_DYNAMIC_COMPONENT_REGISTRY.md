# Research OS Platform Dynamic Component Registry

The Platform component inventory is the canonical metadata registry for Platform components. It is
descriptive and validating; it is not an execution, authorization, merge, or release authority.

## Evolution rules

- Component count is **informational only**. No validator or Final Gate may require a fixed count.
- Required components are explicit through `component.required == true`.
- Optional extensions may be added with `required: false` without changing validator code.
- Lifecycle is schema-driven: `PROPOSED → EXPERIMENTAL → ACTIVE → DEPRECATED → RETIRED`.
- Every dependency must resolve to another registry component.
- Canonical paths, contracts, tests, and evidence are validated from registry metadata.
- Authority is explicit so new components cannot silently become authorization, evidence, runtime, or release authorities.
- Compatibility metadata is required per component; registry schema version and platform contract version evolve independently.
- Unified Final Gate remains the sole release authority.

## Component model

Each component declares `id`, `required`, `class`, `canonical`, `kind`, `lifecycle`,
`dependencies`, `contracts`, `tests`, `evidence`, `gates`, `capabilities`, `authority`,
and `compatibility`.

Recon, governance reporting, Control Center surfaces, and future AI-assisted tooling can consume
the same metadata instead of maintaining another component list.

## Safe evolution

Adding a valid optional component is a registry data change, not a validator-code change.
Removing or retiring a required component requires an explicit contract/governance change and Final
Gate proof.

The registry is intentionally not a second runtime registry. It is the canonical metadata view over
existing implementation authorities.
