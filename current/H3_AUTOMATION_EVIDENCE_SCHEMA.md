# H3 Automation Evidence Schema

Evidence states are explicit:

- `CAPTURED` — identity observed; not a pass.
- `PENDING` — verification has not completed.
- `PASS` — authoritative verification succeeded for the exact SHA.
- `FAIL` — authoritative verification failed.
- `UNKNOWN` — required evidence is missing, conflicting, stale, or unverifiable.

Only `PASS` from authoritative exact-SHA verification can satisfy certification. `CAPTURED`, `PENDING`, and `UNKNOWN` never authorize merge or release.
