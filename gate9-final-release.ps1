$ErrorActionPreference = "Continue"

$base = "http://127.0.0.1:8790"

$headers = @{
    "X-Research-OS-Owner"   = "owner"
    "X-Research-OS-Profile" = "default"
    "X-Research-OS-Session" = "desktop-e2e"
}

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

function SECTION([string]$name) {
    Write-Host ""
    Write-Host $name -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESEARCH OS V3 — GATE 9" -ForegroundColor Cyan
Write-Host " FINAL RELEASE GATE" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "BASE:    $base"
Write-Host "OWNER:   owner"
Write-Host "PROFILE: default"
Write-Host "SESSION: desktop-e2e"
Write-Host ""

# ============================================================
# 1. FINAL RUNTIME HEALTH
# ============================================================

SECTION "[1/10] FINAL RUNTIME HEALTH"

$status = $null

try {

    $status = Invoke-RestMethod `
        -Uri "$base/owner/status" `
        -Headers $headers `
        -ErrorAction Stop

    PASS "runtime reachable"

    if ($status.owner_id -eq "owner") {
        PASS "owner identity"
    }
    else {
        FAIL "owner identity"
    }

    if ($status.profile_id -eq "default") {
        PASS "profile identity"
    }
    else {
        FAIL "profile identity"
    }

    if ($status.session_id -eq "desktop-e2e") {
        PASS "session identity"
    }
    else {
        FAIL "session identity"
    }

    if ($status.service -eq "owner-friend") {
        PASS "owner-friend service"
    }
    else {
        FAIL "owner-friend service"
    }

    if ($status.version -eq "1.3.0-owner") {
        PASS "owner version"
    }
    else {
        FAIL "owner version"
    }

}
catch {

    FAIL "final runtime health"

    Write-Host ""
    Write-Host $_.Exception.Message -ForegroundColor DarkYellow
}

# ============================================================
# 2. V3 BRIDGE FINAL LOCK
# ============================================================

SECTION "[2/10] V3 BRIDGE FINAL LOCK"

if ($null -ne $status) {

    if ($status.v3_bridge.available -eq $true) {
        PASS "V3 bridge available"
    }
    else {
        FAIL "V3 bridge available"
    }

}
else {

    FAIL "V3 bridge status available"
}

$expectedExports = @(
    "BrainCore",
    "UnifiedMasterOrchestrator",
    "SoftwareFactory",
    "FactoryExecutionEngine",
    "ProviderRegistry",
    "OpenAICompatibleProvider",
    "UserContext",
    "UserDataLayout"
)

foreach ($export in $expectedExports) {

    if ($null -ne $status -and
        $status.v3_bridge.exports -contains $export) {

        PASS "V3 export locked: $export"
    }
    else {

        FAIL "V3 export missing: $export"
    }
}

# ============================================================
# 3. CAPABILITY FINAL LOCK
# ============================================================

SECTION "[3/10] CAPABILITY FINAL LOCK"

$expectedCapabilities = @(
    "brain",
    "context",
    "evidence",
    "factory",
    "identity",
    "memory",
    "orchestrator",
    "owner-bundle",
    "persistent-memory",
    "policy",
    "providers",
    "reasoning-summary",
    "skills",
    "tests",
    "tools",
    "v3-bridge"
)

foreach ($capability in $expectedCapabilities) {

    if ($null -ne $status -and
        $status.capabilities -contains $capability) {

        PASS "capability locked: $capability"
    }
    else {

        FAIL "capability missing: $capability"
    }
}

# ============================================================
# 4. PERSISTENCE / MEMORY FINAL LOCK
# ============================================================

SECTION "[4/10] PERSISTENCE / MEMORY FINAL LOCK"

if ($status.memory_persistence -eq "disk") {
    PASS "disk persistence"
}
else {
    FAIL "disk persistence"
}

if ($status.memory_scope -eq "owner/profile/session") {
    PASS "owner/profile/session scope"
}
else {
    FAIL "owner/profile/session scope"
}

if ($status.reasoning_storage -eq "high-level-summary-only") {
    PASS "reasoning storage policy"
}
else {
    FAIL "reasoning storage policy"
}

# ============================================================
# 5. PROVIDER / TOOL FINAL LOCK
# ============================================================

SECTION "[5/10] PROVIDER / TOOL FINAL LOCK"

if ($status.providers -contains "owner-mock") {
    PASS "owner provider"
}
else {
    FAIL "owner provider"
}

if ($status.tools -contains "echo") {
    PASS "echo tool"
}
else {
    FAIL "echo tool"
}

if ($status.tools -contains "summarize") {
    PASS "summarize tool"
}
else {
    FAIL "summarize tool"
}

# ============================================================
# 6. ORCHESTRATOR / SCALE FINAL LOCK
# ============================================================

SECTION "[6/10] ORCHESTRATOR / SCALE FINAL LOCK"

if ($status.scale_authority -eq "v3-unified-master-orchestrator") {
    PASS "V3 scale authority"
}
else {
    FAIL "V3 scale authority"
}

if ($status.helper_scheduler.activation -eq "bounded-adaptive") {
    PASS "bounded adaptive scheduler"
}
else {
    FAIL "bounded adaptive scheduler"
}

if ([int64]$status.helper_scheduler.max_active_workers -eq 128) {
    PASS "worker bound 128"
}
else {
    FAIL "worker bound 128"
}

if ([int64]$status.helper_scheduler.max_logical_helpers -eq 10000000000) {
    PASS "logical helper bound 10^10"
}
else {
    FAIL "logical helper bound 10^10"
}

# ============================================================
# 7. GATE SCRIPT INTEGRITY
# ============================================================

SECTION "[7/10] PREVIOUS GATE ARTIFACTS"

$gateArtifacts = @(
    "gate5-runtime.ps1",
    "gate6-functional-e2e.ps1",
    "gate7-persistence-recovery.ps1",
    "gate8-integrity-release.ps1"
)

foreach ($artifact in $gateArtifacts) {

    if (Test-Path ".\$artifact") {

        $item = Get-Item ".\$artifact"

        if ($item.Length -gt 100) {
            PASS "gate artifact valid: $artifact"
        }
        else {
            WARN "gate artifact unusually small: $artifact"
        }

    }
    else {

        FAIL "gate artifact missing: $artifact"
    }
}

# ============================================================
# 8. GIT FINAL INTEGRITY
# ============================================================

SECTION "[8/10] GIT FINAL INTEGRITY"

if (Test-Path ".git") {
    PASS "Git repository present"
}
else {
    FAIL "Git repository present"
}

$branch = ""

try {

    $branch = git branch --show-current 2>$null

    if ($LASTEXITCODE -eq 0 -and $branch) {

        PASS "Git branch readable"

        Write-Host ""
        Write-Host "BRANCH: $branch" -ForegroundColor Cyan
    }
    else {

        FAIL "Git branch readable"
    }

}
catch {

    FAIL "Git branch inspection"
}

$commit = ""

try {

    $commit = git rev-parse --short HEAD 2>$null

    if ($LASTEXITCODE -eq 0 -and $commit) {

        PASS "HEAD commit readable"

        Write-Host "HEAD:   $commit" -ForegroundColor Cyan
    }
    else {

        FAIL "HEAD commit readable"
    }

}
catch {

    FAIL "HEAD inspection"
}

try {

    git diff --check 2>$null | Out-Null

    if ($LASTEXITCODE -eq 0) {
        PASS "Git whitespace integrity"
    }
    else {
        FAIL "Git whitespace integrity"
    }

}
catch {

    WARN "Git diff check unavailable"
}

# ============================================================
# 9. WORKTREE / RELEASE SAFETY
# ============================================================

SECTION "[9/10] WORKTREE / RELEASE SAFETY"

try {

    $statusShort = @(git status --short 2>$null)

    if ($LASTEXITCODE -eq 0) {

        if ($statusShort.Count -eq 0) {

            PASS "working tree clean"

        }
        else {

            WARN "working tree has uncommitted changes"

            Write-Host ""
            Write-Host "Working tree changes:" -ForegroundColor Yellow

            foreach ($line in $statusShort) {
                Write-Host "  $line"
            }
        }

    }
    else {

        WARN "unable to inspect working tree"
    }

}
catch {

    WARN "working tree inspection unavailable"
}

# ============================================================
# 10. FINAL LIVE RECHECK
# ============================================================

SECTION "[10/10] FINAL LIVE RECHECK"

try {

    $final = Invoke-RestMethod `
        -Uri "$base/owner/status" `
        -Headers $headers `
        -ErrorAction Stop

    if ($final.owner_id -eq "owner" -and
        $final.profile_id -eq "default" -and
        $final.session_id -eq "desktop-e2e" -and
        $final.service -eq "owner-friend" -and
        $final.version -eq "1.3.0-owner" -and
        $final.v3_bridge.available -eq $true) {

        PASS "final runtime contract"

    }
    else {

        FAIL "final runtime contract"
    }

}
catch {

    FAIL "final live runtime check"
}

# ============================================================
# FINAL RELEASE DECISION
# ============================================================

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GATE 9 FINAL RELEASE RESULT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host ("PASSED:   " + $passed) -ForegroundColor Green
Write-Host ("FAILED:   " + $failed) -ForegroundColor Red
Write-Host ("WARNINGS: " + $warnings) -ForegroundColor Yellow

Write-Host ""

if ($failed -eq 0) {

    Write-Host "============================================================" -ForegroundColor Green
    Write-Host " FINAL RELEASE GATE: PASS" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""

    Write-Host "RESEARCH OS V3 RELEASE CANDIDATE: READY" `
        -ForegroundColor Green

    Write-Host ""
    Write-Host "All blocking final-gate checks passed." `
        -ForegroundColor Green

    Write-Host ""
    Write-Host "RELEASE STATE: LOCK" -ForegroundColor Cyan

    Write-Host ""
    Write-Host "Do not modify previously passed gates unless a new" `
        -ForegroundColor Yellow

    Write-Host "regression or explicit release requirement appears." `
        -ForegroundColor Yellow

}
else {

    Write-Host "============================================================" -ForegroundColor Red
    Write-Host " FINAL RELEASE GATE: FAIL" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""

    Write-Host "RELEASE BLOCKED." -ForegroundColor Red

    Write-Host ""
    Write-Host "Investigate ONLY the failed checks above." `
        -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " FINAL GATE PROCESS FINISHED" -ForegroundColor Cyan
Write-Host " TERMINAL REMAINS OPEN" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
