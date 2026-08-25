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
Write-Host " RESEARCH OS V3 — GATE 8" -ForegroundColor Cyan
Write-Host " INTEGRITY / EVIDENCE / RELEASE READINESS" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "BASE:    $base"
Write-Host "OWNER:   owner"
Write-Host "PROFILE: default"
Write-Host "SESSION: desktop-e2e"
Write-Host ""

# ------------------------------------------------------------
# 1. RUNTIME HEALTH
# ------------------------------------------------------------

SECTION "[1/8] RUNTIME HEALTH"

try {

    $status = Invoke-RestMethod `
        -Uri "$base/owner/status" `
        -Headers $headers `
        -ErrorAction Stop

    PASS "owner status endpoint"

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
        PASS "service identity"
    }
    else {
        FAIL "service identity"
    }

    if ($status.version -eq "1.3.0-owner") {
        PASS "service version"
    }
    else {
        FAIL "service version"
    }

    if ($status.v3_bridge.available -eq $true) {
        PASS "V3 bridge availability"
    }
    else {
        FAIL "V3 bridge availability"
    }

}
catch {

    FAIL "runtime health request"

    Write-Host ""
    Write-Host "Runtime response:" -ForegroundColor DarkYellow
    Write-Host $_.Exception.Message -ForegroundColor DarkYellow
}

# ------------------------------------------------------------
# 2. V3 EXPORT INTEGRITY
# ------------------------------------------------------------

SECTION "[2/8] V3 EXPORT INTEGRITY"

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

if ($null -ne $status -and $null -ne $status.v3_bridge.exports) {

    foreach ($export in $expectedExports) {

        if ($status.v3_bridge.exports -contains $export) {
            PASS "export: $export"
        }
        else {
            FAIL "export: $export"
        }
    }

}
else {

    FAIL "V3 export list available"
}

# ------------------------------------------------------------
# 3. CAPABILITY INTEGRITY
# ------------------------------------------------------------

SECTION "[3/8] CAPABILITY INTEGRITY"

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

if ($null -ne $status -and $null -ne $status.capabilities) {

    foreach ($capability in $expectedCapabilities) {

        if ($status.capabilities -contains $capability) {
            PASS "capability: $capability"
        }
        else {
            FAIL "capability: $capability"
        }
    }

}
else {

    FAIL "capability list available"
}

# ------------------------------------------------------------
# 4. PERSISTENCE / POLICY INTEGRITY
# ------------------------------------------------------------

SECTION "[4/8] PERSISTENCE / POLICY INTEGRITY"

if ($status.memory_persistence -eq "disk") {
    PASS "disk persistence"
}
else {
    FAIL "disk persistence"
}

if ($status.memory_scope -eq "owner/profile/session") {
    PASS "owner/profile/session memory scope"
}
else {
    FAIL "owner/profile/session memory scope"
}

if ($status.reasoning_storage -eq "high-level-summary-only") {
    PASS "reasoning storage policy"
}
else {
    FAIL "reasoning storage policy"
}

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

# ------------------------------------------------------------
# 5. ORCHESTRATOR / SCALE INTEGRITY
# ------------------------------------------------------------

SECTION "[5/8] ORCHESTRATOR / SCALE INTEGRITY"

if ($status.scale_authority -eq "v3-unified-master-orchestrator") {
    PASS "V3 unified master orchestrator authority"
}
else {
    FAIL "V3 unified master orchestrator authority"
}

if ($status.helper_scheduler.activation -eq "bounded-adaptive") {
    PASS "bounded adaptive scheduler"
}
else {
    FAIL "bounded adaptive scheduler"
}

if ([int64]$status.helper_scheduler.max_active_workers -eq 128) {
    PASS "max active workers = 128"
}
else {
    FAIL "max active workers = 128"
}

if ([int64]$status.helper_scheduler.max_logical_helpers -eq 10000000000) {
    PASS "max logical helpers = 10^10"
}
else {
    FAIL "max logical helpers = 10^10"
}

# ------------------------------------------------------------
# 6. REPOSITORY INTEGRITY
# ------------------------------------------------------------

SECTION "[6/8] REPOSITORY INTEGRITY"

if (Test-Path ".git") {
    PASS "Git repository"
}
else {
    FAIL "Git repository"
}

try {

    $branch = git branch --show-current 2>$null

    if ($LASTEXITCODE -eq 0 -and $branch) {
        PASS "current Git branch"
        Write-Host "  Branch: $branch" -ForegroundColor Cyan
    }
    else {
        FAIL "current Git branch"
    }

}
catch {

    FAIL "Git branch inspection"
}

try {

    $commit = git rev-parse --short HEAD 2>$null

    if ($LASTEXITCODE -eq 0 -and $commit) {
        PASS "HEAD commit available"
        Write-Host "  HEAD: $commit" -ForegroundColor Cyan
    }
    else {
        FAIL "HEAD commit available"
    }

}
catch {

    FAIL "Git HEAD inspection"
}

try {

    git diff --check 2>$null | Out-Null

    if ($LASTEXITCODE -eq 0) {
        PASS "Git diff whitespace integrity"
    }
    else {
        FAIL "Git diff whitespace integrity"
    }

}
catch {

    WARN "Git diff check unavailable"
}

# ------------------------------------------------------------
# 7. REQUIRED GATE ARTIFACTS
# ------------------------------------------------------------

SECTION "[7/8] GATE ARTIFACT INTEGRITY"

$requiredArtifacts = @(
    "gate5-runtime.ps1",
    "gate6-functional-e2e.ps1",
    "gate7-persistence-recovery.ps1"
)

foreach ($artifact in $requiredArtifacts) {

    if (Test-Path ".\$artifact") {
        PASS "artifact: $artifact"
    }
    else {
        WARN "artifact missing: $artifact"
    }
}

# Search for likely evidence directories without modifying anything.

$evidenceCandidates = @(
    ".\evidence",
    ".\artifacts",
    ".\reports",
    ".\ResearchOSRuntime",
    ".\ResearchOS",
    ".\runtime"
)

$foundEvidence = $false

foreach ($path in $evidenceCandidates) {

    if (Test-Path $path) {

        $foundEvidence = $true

        PASS "evidence/runtime path: $path"
    }
}

if (-not $foundEvidence) {

    WARN "no standard evidence directory detected"
}

# ------------------------------------------------------------
# 8. FINAL RELEASE READINESS
# ------------------------------------------------------------

SECTION "[8/8] RELEASE READINESS"

$gateFiles = @(
    "gate5-runtime.ps1",
    "gate6-functional-e2e.ps1",
    "gate7-persistence-recovery.ps1"
)

foreach ($gateFile in $gateFiles) {

    if (Test-Path ".\$gateFile") {

        try {

            $size = (Get-Item ".\$gateFile").Length

            if ($size -gt 100) {
                PASS "non-empty gate script: $gateFile"
            }
            else {
                WARN "very small gate script: $gateFile"
            }

        }
        catch {

            WARN "could not inspect: $gateFile"
        }

    }
}

# Verify server remains reachable after all previous gates.

try {

    $finalStatus = Invoke-RestMethod `
        -Uri "$base/owner/status" `
        -Headers $headers `
        -ErrorAction Stop

    if ($finalStatus.owner_id -eq "owner") {
        PASS "runtime stable after Gate 8 checks"
    }
    else {
        FAIL "runtime stable after Gate 8 checks"
    }

}
catch {

    FAIL "runtime final health"
}

# ------------------------------------------------------------
# FINAL RESULT
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GATE 8 RESULT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host ("PASSED:   " + $passed) -ForegroundColor Green
Write-Host ("FAILED:   " + $failed) -ForegroundColor Red
Write-Host ("WARNINGS: " + $warnings) -ForegroundColor Yellow

Write-Host ""

if ($failed -eq 0) {

    Write-Host "GATE 8 - INTEGRITY / RELEASE READINESS: PASS" `
        -ForegroundColor Green

    Write-Host ""
    Write-Host "All blocking integrity checks passed." `
        -ForegroundColor Green

    if ($warnings -gt 0) {

        Write-Host ""
        Write-Host "Non-blocking warnings detected: $warnings" `
            -ForegroundColor Yellow
    }

}
else {

    Write-Host "GATE 8 - INTEGRITY / RELEASE READINESS: FAIL" `
        -ForegroundColor Red

    Write-Host ""
    Write-Host "Do NOT modify previously passed gates blindly." `
        -ForegroundColor Yellow

    Write-Host "Investigate only the failed checks above." `
        -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Gate 8 diagnostic completed." -ForegroundColor Cyan
Write-Host "Terminal remains open." -ForegroundColor Cyan
Write-Host ""
