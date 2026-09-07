# Research OS Constitution

**Status:** PROPOSED / GOVERNANCE CONTRACT
**Scope:** Generator, Autobot, Friend Runtime, CI, Evidence, Mission Control, Build/Install, Release

## Article I — Identity

1. Every authority-relevant operation is bound to an exact source SHA.
2. A captured SHA is immutable for the lifetime of its verification chain.
3. A new code commit creates a new verification identity.
4. SHA mismatch is a hard integrity failure.

## Article II — Evidence

1. Evidence must identify its producer, input SHA, result, schema version, and provenance.
2. Evidence must be validated before downstream consumption.
3. Stale, conflicting, malformed, secret-like, or executable evidence is rejected.
4. Evidence from an earlier SHA cannot certify a later SHA.
5. Planning documents are never evidence of successful execution.

## Article III — Authority

1. Capabilities are explicit and scoped.
2. Read, write, approve, release, and install are distinct authorities.
3. No component may silently escalate its authority.
4. Mission Control is observational/read-only.
5. Release Authority is separate from Generator and Autobot.

## Article IV — Generator

1. Generator creates governed artifacts.
2. Generator records generation provenance.
3. Generator cannot approve its own output.
4. Generated evidence must come from its authoritative workflow.

## Article V — Autobot

1. Autobot may inspect, diagnose, repair, and verify within explicit capability scope.
2. A repair that changes code creates a new SHA.
3. Autobot actions must be auditable.
4. Repair attempts are bounded.
5. Autobot cannot approve itself, bypass gates, or become release authority.

## Article VI — Validation

1. `CAPTURED` is not `PASSED`.
2. `WAITING_FOR_SHA` is pending, not code failure.
3. Actual code/test failures remain failures.
4. Retry is allowed only for explicitly transient failure classes.
5. Integrity and policy failures fail closed.

## Article VII — Build and Release

1. Build identity must match governed source identity.
2. Packages/installers must derive from verified builds.
3. Installed artifacts must have source-to-install provenance.
4. Four user identities remain isolated as four intended EXEs.
5. Release requires the authoritative release gate; no feature branch or agent may self-declare release.

## Article VIII — Runtime and Tools

1. Friend Runtime follows intent -> plan -> policy -> capability -> tool -> result -> evidence.
2. Tools are explicit, health-checked, and capability-gated.
3. Credentials are never embedded in source, binaries, UI projections, or evidence.
4. Future MCP/Web/Computer Use integrations inherit the same authority and evidence rules.

## Article IX — Learning

1. Core Skills are immutable to self-learning.
2. Learned Skills are versioned and provenance-backed.
3. Promotion requires validation, evidence, confidence, and an explicit promotion gate.
4. Rollback and audit history are mandatory for promoted learned behavior.

## Article X — Fail Closed

The following states cannot silently become success:

`UNKNOWN`, `STALE`, `CONFLICT`, `BLOCKED`, `SHA_MISMATCH`, `TIMEOUT`, `MISSING`, `INVALID`, `FAILED`.

## Article XI — Automation Safety

1. Autonomous loops must be bounded.
2. Circuit breakers must halt repeated anomalous behavior.
3. Workflow observability must not become workflow self-dispatch.
4. No hidden autonomous work is considered valid without observable output/evidence.

## Article XII — Release Rule

> No agent can create, modify, or reinterpret evidence in a way that grants itself approval or release authority.

## Enforcement target

This Constitution should eventually be represented by machine-readable policy/validators. Until validator-backed enforcement exists, this document is governance intent only and must not be treated as proof of compliance.
