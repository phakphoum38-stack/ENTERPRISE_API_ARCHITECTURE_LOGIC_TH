# H10 — Learning Promotion

## Purpose

H10 turns verified repair knowledge into a candidate learned skill without allowing the learning layer to become release or authority infrastructure.

## Contract

```text
VERIFIED REPAIR
  -> EVIDENCE
  -> CANDIDATE KNOWLEDGE
  -> VALIDATION
  -> PROMOTION DECISION
  -> LEARNED SKILL
```

Promotion requires explicit verification evidence. Core Skills remain separate and immutable through this boundary.

### Required invariants

- Owner/source identity and bounded correlation are explicit.
- A candidate cannot be promoted without verified evidence.
- Evidence must be tied to the verified repair SHA.
- Core Skills cannot be modified or replaced by learned content.
- Learned content is bounded, deterministic, and defensive-copy safe.
- Secret-like, executable, dynamic, authority-like, or credential-bearing content fails closed.
- Low-confidence or incomplete candidates remain unpromoted.
- No merge, approval, release, install, workflow dispatch, ref mutation, shell/process execution, MCP/Computer Use execution, or evidence fabrication.

The existing self-learning engine and promotion validator remain authoritative for actual learning semantics.
