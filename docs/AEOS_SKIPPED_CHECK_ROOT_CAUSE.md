# AEOS skipped-check verifier root cause

## Incident

AEOS One-Shot Comprehensive Review rejected PR checks when GitHub reported a terminal `SKIPPED` check with a non-`pass` bucket such as `skipping`.

## Root cause

The trusted `pull_request_target` verifier treated the bucket and terminal state as jointly authoritative:

```python
c.get("bucket") != "pass" or c.get("state") not in success_states
```

GitHub can report `state == "SKIPPED"` while the bucket is not `pass`. Since `SKIPPED` is an explicitly accepted terminal state, the bucket check caused a false failure.

## Corrective rule

Terminal state is authoritative for pass/fail classification:

```python
c.get("state") not in success_states
```

with:

```python
success_states = {"SUCCESS", "NEUTRAL", "SKIPPED"}
```

Pending checks remain classified separately by pending state/bucket and continue to be polled.

## Security / trust boundary

The workflow remains a `pull_request_target` verifier that checks out trusted `main` and fetches the exact PR HEAD without executing PR workflow code. This fix changes only terminal-check classification and does not grant merge authority.

## Expected outcome

A terminal `SKIPPED` external check is no longer treated as a failing check solely because its bucket is `skipping`.
