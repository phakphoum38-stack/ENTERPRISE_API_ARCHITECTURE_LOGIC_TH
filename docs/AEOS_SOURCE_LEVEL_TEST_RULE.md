# AEOS Source-Level TEST Rule

If an AEOS task says `TEST`, verify the actual source implementation.

Required trace: registry -> source boundary -> executable entry point -> decision logic -> fail-closed paths -> evidence/provenance -> freshness/independence -> adversarial paths -> regression tests.

No declaration, file existence, CI result, caller boolean, self-attestation, or wrapper around missing implementation can substitute for source verification.
