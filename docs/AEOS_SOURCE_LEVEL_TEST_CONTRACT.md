# AEOS Source-Level TEST Contract

## Rule

In AEOS, **TEST means source-level verification**.

A check is not considered tested merely because:

- a registry entry exists;
- a JSON contract declares the check;
- a boundary file exists;
- CI is green;
- an evidence reference is present; or
- a caller supplies a `PASS`/`VERIFIED` value.

## Required verification path

```text
TEST
  -> locate source boundary
  -> locate executable entry point
  -> trace callers and decision path
  -> inspect PASS condition
  -> inspect FAIL/UNKNOWN/STALE/CONFLICT paths
  -> inspect evidence binding
  -> inspect provenance / independence boundary
  -> inspect negative/adversarial paths
  -> inspect regression coverage
  -> report source-level result
```

## Source test states

- `SOURCE_VERIFIED`: executable source logic was located and inspected.
- `SOURCE_GAP`: the registry requires a source-level check but no executable boundary exists.
- `SOURCE_INVALID`: the declared boundary exists but does not provide executable verification for the named check.
- `EXTERNAL_EVIDENCE`: the check intentionally depends on independently supplied evidence; this is **not** a source TEST and cannot become PASS by declaration.

## Fail-closed rule

A source-level test gap is never silently converted into PASS. The assurance fabric must expose the gap so implementation can be added and regression-tested before certification.

## User-facing simplification

The user only needs to request **TEST**. The system owns the deep source inspection internally.
