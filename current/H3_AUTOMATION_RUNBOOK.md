# H3 Automation Runbook

1. Capture the current main SHA.
2. Re-anchor the working branch to that SHA.
3. Run focused H3 negative/adversarial tests.
4. Run authoritative repository CI at the exact PR head.
5. Validate H2 evidence/provenance lineage.
6. Audit execution, approval, release, merge, and dispatch authority.
7. If any state is stale, missing, conflicting, or unknown, stop and diagnose.
8. Certify only after all authoritative gates pass.
9. Merge remains owner-controlled until a separate autonomous-merge contract is certified.
10. After merge, verify main again and create the next certified baseline.
