# Research OS H21–H27 — Root-Cause Forensics: unittest Namespace Collision

## Status

**Root cause confirmed. Shared CI topology fix applied to the H21 stack.**

This record preserves the causal chain separately from the feature contracts. It is evidence/context only; it does not grant authority and does not alter historical canonical evidence.

## Causal chain

```text
H21 #305
  ↓ first CI detector
H22 #306
H23 #307
H24 #308
H25 #309
H26 #310
H27 #311
  ↓
shared Python import/discovery topology
```

### Detector vs introducer

- **First detector:** PR #305 (H21).
- **#305 is not proven to be the defect introducer.** The namespace collision was latent in the repository topology before the H21 workflow exposed it.
- The defect is therefore classified as a **shared infrastructure/topology defect**, not seven independent feature defects.

## Root cause

The repository contains two different `tools` namespaces relevant to this test topology:

1. `owner_special/research_os_friend/tools.py` — the internal `Tool` / `ToolRegistry` module.
2. `tools/research_os_api/github_status.py` — the repository-root `tools` namespace package.

`owner_special/research_os_friend/catalog.py` intentionally imports both:

```python
from .tools import Tool, ToolRegistry
from tools.research_os_api.github_status import GitHubStatusError, dashboard as github_dashboard
```

When `unittest discover` is started with `-s owner_special/research_os_friend` and no explicit top-level directory, discovery can place the start directory on `sys.path`. In that topology, `tools` can resolve to `owner_special/research_os_friend/tools.py`, which is a module rather than a package. The absolute import then fails with:

```text
ModuleNotFoundError: No module named 'tools.research_os_api'; 'tools' is not a package
```

## Correct boundary

The learning-contract workflow now makes the repository root the explicit top-level discovery directory while retaining the focused start directory:

```bash
python -m unittest discover \
  -s owner_special/research_os_friend \
  -t . \
  -p 'test_*.py' \
  -v
```

This fixes the **test topology**, not production imports. No `sys.path` mutation was added to production code, no import error was swallowed, and `tools.py` was not renamed.

## Why this is the root fix

The change is deliberately centralized in the shared learning-contract workflow. All stacked H21–H27 branches inherit the corrected topology through the H21 base branch.

Expected regression property:

> Any H21–H27 learning-contract test run must resolve repository-root `tools` as the namespace containing `tools.research_os_api`, while resolving the internal tool registry through the relative `owner_special.research_os_friend.tools` import.

## Evidence references

- H21 PR #305 introduced the learning-contract workflow with the failing discovery topology.
- `owner_special/research_os_friend/tools.py` defines the internal `Tool` / `ToolRegistry` module.
- `owner_special/research_os_friend/catalog.py` imports both namespaces, making the collision observable.
- The fix changes only the unittest discovery topology from `-s ...` to `-s ... -t .`.

## Preservation rule

This document does not rewrite or replace any historical H21–H27 evidence. It records the root-cause interpretation and the shared remediation so downstream review can distinguish:

```text
first detector ≠ defect introducer
shared cause  → shared fix
```
