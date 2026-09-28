# AEOS TEST Execution Policy

When an AEOS work item says `TEST`, the expected operation is source-level verification of the implementation behind every named check.

## Minimum source trace

1. Registry check -> declared boundary
2. Boundary -> executable symbol/entry point
3. Entry point -> decision logic
4. Decision -> PASS/FAIL/UNKNOWN/STALE/CONFLICT behavior
5. Decision -> evidence and provenance binding
6. Evidence -> independence and freshness constraints
7. Source -> negative/adversarial behavior
8. Source -> regression tests

## Prohibited substitutions

The following do not satisfy TEST by themselves:

- file existence;
- JSON declaration;
- check-name presence;
- CI status;
- caller-provided booleans;
- self-attested evidence;
- a green wrapper around an unimplemented check.

## Completion rule

The full assurance universe is only source-tested when every required check has either:

- a verified executable source implementation with regression coverage; or
- an explicitly external evidence contract that is independently bound and separately verified.

Any unresolved source gap is a certification blocker.
