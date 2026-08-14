# V3 Validation Lineage

This file records the exact-SHA certification policy for the canonical V3 line.

- Any change to V3 after synchronizing with `main` requires validation on the new exact head SHA.
- Core, provider-hardening, factory-execution, and Candidate evidence must refer to that same SHA before merge.
- A previously successful Candidate from an older SHA is reference evidence only and does not certify a newer head.
- Candidate validation includes Windows app build, ServiceHost build, Setup EXE creation, clean install, app-to-service E2E, in-place upgrade, uninstall, data preservation, and evidence generation.

This policy preserves exact-SHA release lineage while allowing `main` synchronization without treating old artifacts as current certification.
