# Research OS H6 — Controlled Automation Boundary

## Purpose

H6 defines the final safety boundary for future MCP, Computer Use, and external automation. The contract is capability-gated and policy-only: it validates whether an action may be proposed, but does not execute the action.

## Flow

```text
Automation request
      ↓
H6 policy boundary
      ↓
identity + capability + target + risk validation
      ↓
ALLOW / DENY / REQUIRE_APPROVAL
      ↓
separate execution authority
```

## Required controls

- exact Owner identity;
- exact source SHA;
- bounded correlation ID;
- explicit capability allowlist;
- explicit target allowlist;
- action type allowlist;
- dry-run support;
- approval required for side effects;
- no credentials in requests or targets;
- no arbitrary shell/process execution;
- no arbitrary MCP server/provider invocation;
- no implicit Computer Use control;
- deterministic decision output.

## Decision model

- `ALLOW_READ_ONLY` — bounded read-only operation may proceed through a separately authorized executor;
- `REQUIRE_APPROVAL` — side-effecting operation needs an explicit approval boundary;
- `DENY` — identity, capability, target, risk, or content is unsafe.

H6 itself is never the executor and never grants approval.

## Target policy

Targets must be explicit and bounded. URLs require a permitted scheme and host allowlist. File targets require an explicit permitted root. Commands are denied by default rather than interpreted heuristically.

## Evidence

H6 consumes decision context but never fabricates execution evidence. An executor must return fresh evidence bound to the same source SHA and correlation ID before any downstream system may treat an action as completed.

## Authority

H6 cannot merge, release, install, dispatch workflows, mutate Git refs, rewrite evidence, grant capabilities, approve itself, or replace the release authority model.
