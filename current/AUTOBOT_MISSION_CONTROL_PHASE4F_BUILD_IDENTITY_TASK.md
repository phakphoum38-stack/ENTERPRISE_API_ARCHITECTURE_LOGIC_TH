# Autobot Mission Control Phase 4F — Build Identity Projection Task

## Objective
Implement a read-only Mission Control projection for build/release identity and installed-release provenance, using existing canonical provenance gates.

## Contract
- Presentation only; never become a build or release authority.
- Reuse existing Build Identity Gate and Installed Owner Release Provenance Gate evidence.
- Show exact commit/source identity only when already evidenced by canonical sources.
- Never infer identity from filenames alone.
- Fail closed for missing, conflicting, stale, or unknown identity evidence.
- Owner-scoped and deterministic.
- Bounded output and explicit truncation.

## Safety
No build, package, install, uninstall, release, signing, execution, network, credential, policy, approval, authorization, MCP, Computer Use, browser, or OS-input operations.

## Tests / evidence
Cover valid identity, mismatch, missing provenance, conflicting SHA, stale evidence, bounded output, deterministic ordering, secret redaction, and input immutability. Produce a clean first-class `.diff` artifact and machine-readable evidence.

## Workflow discipline
Do not manually dispatch workflows. Do not merge from this task. Record exact base/head SHAs and authoritative CI results in the completion report.
