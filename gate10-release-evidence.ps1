$ErrorActionPreference = "Stop"

Set-Location "C:\Users\phakp\ENTERPRISE_API_ARCHITECTURE_LOGIC_TH"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESEARCH OS V3 — GATE 10" -ForegroundColor Cyan
Write-Host " RELEASE EVIDENCE / COMMIT PRECHECK" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$passed = 0
$failed = 0
$warnings = 0

function PASS([string]$name) {
    $script:passed++
    Write-Host "PASS  $name" -ForegroundColor Green
}

function FAIL([string]$name) {
    $script:failed++
    Write-Host "FAIL  $name" -ForegroundColor Red
}

function WARN([string]$name) {
    $script:warnings++
    Write-Host "WARN  $name" -ForegroundColor Yellow
}

# ------------------------------------------------------------
# 1. GIT REPOSITORY
# ------------------------------------------------------------

Write-Host "[1/7] GIT REPOSITORY" -ForegroundColor Yellow

try {
    $root = git rev-parse --show-toplevel 2>$null

    if ($LASTEXITCODE -eq 0 -and $root) {
        PASS "Git repository"
    } else {
        FAIL "Git repository"
    }
}
catch {
    FAIL "Git repository"
}

# ------------------------------------------------------------
# 2. CURRENT BRANCH / HEAD
# ------------------------------------------------------------

Write-Host ""
Write-Host "[2/7] RELEASE SOURCE" -ForegroundColor Yellow

$branch = git branch --show-current
$head = git rev-parse --short HEAD

if ($branch) {
    PASS "current branch"
    Write-Host "  BRANCH: $branch"
} else {
    FAIL "current branch"
}

if ($head) {
    PASS "HEAD commit"
    Write-Host "  HEAD:   $head"
} else {
    FAIL "HEAD commit"
}

# ------------------------------------------------------------
# 3. WHITESPACE / DIFF CHECK
# ------------------------------------------------------------

Write-Host ""
Write-Host "[3/7] DIFF INTEGRITY" -ForegroundColor Yellow

git diff --check

if ($LASTEXITCODE -eq 0) {
    PASS "git diff --check"
} else {
    FAIL "git diff --check"
}

# ------------------------------------------------------------
# 4. REQUIRED GATE ARTIFACTS
# ------------------------------------------------------------

Write-Host ""
Write-Host "[4/7] GATE ARTIFACTS" -ForegroundColor Yellow

$required = @(
    "gate5-runtime.ps1",
    "gate6-functional-e2e.ps1",
    "gate7-persistence-recovery.ps1",
    "gate8-integrity-release.ps1",
    "gate9-final-release.ps1"
)

foreach ($file in $required) {

    if (Test-Path ".\$file") {

        $item = Get-Item ".\$file"

        if ($item.Length -gt 0) {
            PASS "artifact: $file"
        } else {
            FAIL "artifact empty: $file"
        }

    } else {
        FAIL "artifact missing: $file"
    }
}

# ------------------------------------------------------------
# 5. EVIDENCE ARTIFACT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[5/7] RELEASE EVIDENCE" -ForegroundColor Yellow

$evidence = "owner_desktop_e2e_gate_evidence.json"

if (Test-Path ".\$evidence") {

    try {
        $json = Get-Content ".\$evidence" -Raw |
            ConvertFrom-Json

        if ($json) {
            PASS "owner desktop E2E evidence"
        } else {
            FAIL "owner desktop E2E evidence"
        }
    }
    catch {
        FAIL "owner desktop E2E evidence parse"
        Write-Host "  $($_.Exception.Message)" -ForegroundColor DarkYellow
    }

} else {
    WARN "owner desktop E2E evidence file missing"
}

# ------------------------------------------------------------
# 6. WORKTREE INVENTORY
# ------------------------------------------------------------

Write-Host ""
Write-Host "[6/7] WORKTREE INVENTORY" -ForegroundColor Yellow

$statusLines = @(git status --short)

if ($statusLines.Count -eq 0) {

    PASS "working tree clean"

} else {

    WARN "working tree contains changes"

    Write-Host ""
    Write-Host "Release candidate changes:" -ForegroundColor Cyan

    foreach ($line in $statusLines) {
        Write-Host "  $line"
    }
}

# ------------------------------------------------------------
# 7. RELEASE DECISION
# ------------------------------------------------------------

Write-Host ""
Write-Host "[7/7] RELEASE DECISION" -ForegroundColor Yellow

Write-Host ""

if ($failed -eq 0) {

    PASS "all blocking Gate 10 checks"

} else {

    FAIL "all blocking Gate 10 checks"
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GATE 10 RESULT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "PASSED:   $passed" -ForegroundColor Green
Write-Host "FAILED:   $failed" -ForegroundColor Red
Write-Host "WARNINGS: $warnings" -ForegroundColor Yellow
Write-Host ""

if ($failed -eq 0) {

    Write-Host "GATE 10 - RELEASE EVIDENCE PRECHECK: PASS" `
        -ForegroundColor Green

    Write-Host ""
    Write-Host "Release evidence is ready for commit." `
        -ForegroundColor Green

    Write-Host ""
    Write-Host "IMPORTANT:" -ForegroundColor Yellow
    Write-Host "No previously passed Gate should be modified." `
        -ForegroundColor Yellow

    exit 0

} else {

    Write-Host "GATE 10 - RELEASE EVIDENCE PRECHECK: FAIL" `
        -ForegroundColor Red

    exit 1
}
