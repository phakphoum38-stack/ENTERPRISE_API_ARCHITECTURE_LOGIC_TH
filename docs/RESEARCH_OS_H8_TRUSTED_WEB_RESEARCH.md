# Research OS H8 — Trusted Web Research

H8 defines a source-selection and evidence boundary for Autobot research. Research may inform diagnosis, but it cannot replace CI, identity, provenance, or release authority.

## Source trust

Preferred sources are official documentation, official repositories, and maintainer-authored material. Community sources may provide context but are not authoritative by themselves.

## Matching

Research records must identify the observed URL/host, source kind, version/environment context, and correlation ID. Version mismatches or missing environment context remain UNKNOWN rather than being guessed.

## Safety

URLs are bounded and restricted to approved schemes. Secret-like, credential-like, executable, shell, dynamic, and authority content is rejected. Research is read-only and produces no workflow dispatch, ref mutation, install, merge, release, or approval action.
