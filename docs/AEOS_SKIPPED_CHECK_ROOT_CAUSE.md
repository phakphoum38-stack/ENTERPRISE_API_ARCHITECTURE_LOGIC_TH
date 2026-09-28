# AEOS skipped-check verifier root cause

The AEOS One-Shot Comprehensive Review verifier rejected a terminal GitHub Actions check reported as `state == "SKIPPED"` because its `bucket` was `skipping` rather than `pass`.

The previous condition treated both fields as authoritative:

```python
c.get("bucket") != "pass" or c.get("state") not in success_states
```

That is incorrect when `SKIPPED` is an explicitly accepted terminal state. The corrective rule is state-based:

```python
success_states = {"SUCCESS", "NEUTRAL", "SKIPPED"}
bad = [
    c for c in external
    if c not in pending
    and c.get("state") not in success_states
]
```

Pending checks remain separately classified and polled. The trusted `pull_request_target` boundary and non-authorizing review certificate remain unchanged.
