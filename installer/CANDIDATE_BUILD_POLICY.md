# Candidate Build Policy

Research OS uses a write-first, build-once candidate workflow.

## Rule

- Normal development commits run Core CI only.
- Core CI may build reusable component artifacts, but it must not build the Setup EXE.
- A final commit containing `[candidate]` in the commit message explicitly marks the code as ready for the full candidate chain.
- The final candidate chain is:
  1. Runtime Smoke
  2. Build Installer
  3. Installer Validation
  4. Exact-SHA Candidate Evidence Gate
- The installer workflow uses exact-SHA concurrency so duplicate requests for the same candidate SHA cannot produce parallel installer builds.
- Release and merge remain separate explicit actions and are not performed by the candidate chain.

This policy prevents repeated Setup builds while code is still being written or adjusted.
