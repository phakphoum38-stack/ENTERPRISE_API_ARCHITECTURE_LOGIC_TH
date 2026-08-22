#!/usr/bin/env bash
set -euo pipefail

# Project Execution Master Guardrail
# Purpose: keep project execution on-plan and prevent accidental scope expansion.
# Policy: Passed = Locked; Evidence before Gate; No critical evidence = no new scope.

PROJECT_ROOT="${PROJECT_ROOT:-.}"
MAIN_BRANCH="${MAIN_BRANCH:-main}"
NODE_MAJOR="${NODE_MAJOR:-24}"

fail() {
  echo "BLOCKED: $1" >&2
  exit 1
}

cd "$PROJECT_ROOT"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "Not a Git repository."

current_branch="$(git branch --show-current)"
echo "PROJECT EXECUTION MASTER GUARDRAIL"
echo "Current branch: ${current_branch}"
echo "Main branch: ${MAIN_BRANCH}"
echo "Node.js baseline: ${NODE_MAJOR}"

echo "[1/6] Repository safety"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "WARNING: working tree has uncommitted changes. Review before destructive Git operations."
fi

if [[ "$current_branch" == "$MAIN_BRANCH" ]]; then
  echo "WARNING: direct implementation on ${MAIN_BRANCH} is discouraged; use a feature/agent branch and PR."
fi

echo "[2/6] Node.js ${NODE_MAJOR} baseline"
if command -v node >/dev/null 2>&1; then
  node_major="$(node -p 'process.versions.node.split(".")[0]')"
  [[ "$node_major" == "$NODE_MAJOR" ]] || fail "Node.js ${NODE_MAJOR} required; detected ${node_major}."
  echo "Node.js ${node_major}: OK"
else
  echo "Node.js not installed locally; JavaScript runtime check deferred to CI."
fi

echo "[3/6] Execution order"
cat <<'EOF'
A-E  Release Critical
F-L  Post-Final Evolution
M    Long-Term Guardrails
N    Meta-Governance
O    Product Readiness
P    Closure & Continuity
EOF

echo "[4/6] Evidence rule"
cat <<'EOF'
Every completed item must have:
  implementation -> automated test -> CI -> evidence -> gate decision
PASS    = lock the completed scope
FAIL    = fix only the proven failure
BLOCKED = record the blocker; do not bypass the gate
EOF

echo "[5/6] Scope guard"
cat <<'EOF'
Do not create a new project category unless evidence shows:
  - a critical bug,
  - a security finding,
  - a measured performance gap,
  - a formally accepted user requirement, or
  - an architecture decision that requires it.
Do not modify a locked component without new evidence.
EOF

echo "[6/6] Release gate checklist"
cat <<'EOF'
[ ] Runtime / Worker
[ ] Reliability / Load
[ ] Observability
[ ] E2E / QA / Contract
[ ] Security / Governance
[ ] Production Readiness
[ ] Final Evidence Pack
[ ] Canonical SHA / Release baseline
[ ] Known Issues reviewed
[ ] Rollback / Continuity verified
[ ] Final Gate passed
EOF

echo "READY: guardrail checks completed; no automatic changes performed."
