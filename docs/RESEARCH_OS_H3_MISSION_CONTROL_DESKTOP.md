# Research OS H3 — Mission Control / Desktop

**Status:** IMPLEMENTATION DRAFT — verification required
**Base:** `9870fefe2d27f77976e217c52d81a73e082c7d4a`

## Purpose

H3 turns the validated H2 evidence/provenance model and the existing Mission Control projections into a desktop-facing, read-only observer contract. The desktop is a projection consumer, not an authority engine.

## Lineage

```text
Exact source SHA
  -> H0 identity
  -> H1 generator/autobot boundary
  -> H2 evidence/provenance
  -> H3 Mission Control/Desktop
```

A desktop view never manufactures a commit SHA, CI result, artifact digest, approval, release decision, or provenance record. Runtime/generated evidence remains produced by CI and upstream authoritative producers.

## Boundary

Allowed:
- consume already validated evidence/provenance records;
- bind the view to one exact source SHA and run correlation;
- expose deterministic status, provenance, and evidence summaries;
- preserve explicit PASS/FAIL/PENDING/UNKNOWN/BLOCKED states;
- render bounded text, metrics, tables, timelines, and health summaries.

Forbidden:
- workflow dispatch;
- merge/approve/release/install authority;
- shell/process execution;
- MCP or Computer Use execution;
- credential handling;
- mutation of source evidence;
- changing release authority;
- inventing missing evidence or upgrading UNKNOWN/FAIL to PASS.

## Fail-closed rules

1. Missing or malformed source identity blocks the view.
2. A stale SHA or correlation ID blocks the view.
3. Conflicting provenance blocks the view.
4. Secret-like or authority-bearing payloads are rejected.
5. Unknown state remains UNKNOWN; it is never inferred as success.
6. Presentation truncation is explicit and deterministic.
7. The projection is immutable from the caller's perspective.

## Desktop contract

The desktop adapter accepts an H2 `EvidenceRecord` plus optional `ProvenanceChain` and returns a bounded model with:

- `schema`
- `owner_id`
- `read_only: true`
- `source_sha`
- `correlation_id`
- `evidence_type`
- `status`
- `provenance_fingerprint`
- `artifact_sha256` when present
- bounded descriptive `summary`
- explicit `truncated` metadata

The model is presentation data only. It contains no executable callbacks, commands, dynamic code, approval fields, or release controls.

## Verification

CI remains authoritative. H3 tests cover identity binding, freshness, provenance linkage, status preservation, deterministic output, bounds, immutability, secret-like rejection, authority rejection, and forbidden execution-shaped fields.
