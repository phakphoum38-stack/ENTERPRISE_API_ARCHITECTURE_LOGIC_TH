# AEOS TEST = Source-Level Verification

`TEST` is a user-facing shorthand for deep implementation verification.

For every required check, the verifier must trace:

- registry entry to source boundary;
- source boundary to executable symbol/entry point;
- entry point to the actual decision logic;
- PASS and fail-closed negative paths;
- evidence/provenance binding;
- freshness and independence boundaries;
- adversarial behavior and regression coverage.

A declaration, filename, CI result, caller boolean, or self-attested evidence is not sufficient.

If a required check has no executable implementation, the result is `SOURCE_GAP` and certification is blocked. If the declared implementation does not actually implement the named check, the result is `SOURCE_INVALID` and certification is blocked.
