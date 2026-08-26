$ErrorActionPreference = "Stop"

$base = "http://127.0.0.1:8790"

$headers = @{
    "X-Research-OS-Owner"   = "owner"
    "X-Research-OS-Profile" = "default"
    "X-Research-OS-Session" = "desktop-e2e"
}

$passed = 0
$failed = 0

function PASS([string]$name) {
    $script:passed++
    Write-Host "PASS  $name" -ForegroundColor Green
}

function FAIL([string]$name) {
    $script:failed++
    Write-Host "FAIL  $name" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESEARCH OS V3 — GATE 5 RUNTIME CONTRACT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ------------------------------------------------------------
# 1. OWNER STATUS
# ------------------------------------------------------------

Write-Host "[1/6] OWNER IDENTITY" -ForegroundColor Yellow

$status = Invoke-RestMethod `
    -Uri "$base/owner/status" `
    -Headers $headers `
    -ErrorAction Stop

if ($status.owner_id -eq "owner") {
    PASS "owner identity"
} else {
    FAIL "owner identity"
}

if ($status.profile_id -eq "default") {
    PASS "profile scope"
} else {
    FAIL "profile scope"
}

if ($status.session_id -eq "desktop-e2e") {
    PASS "session scope"
} else {
    FAIL "session scope"
}

# ------------------------------------------------------------
# 2. SERVICE CONTRACT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[2/6] SERVICE CONTRACT" -ForegroundColor Yellow

if ($status.service -eq "owner-friend") {
    PASS "owner-friend service"
} else {
    FAIL "owner-friend service"
}

if ($status.version -eq "1.3.0-owner") {
    PASS "owner version"
} else {
    FAIL "owner version"
}

# ------------------------------------------------------------
# 3. V3 BRIDGE
# ------------------------------------------------------------

Write-Host ""
Write-Host "[3/6] V3 BRIDGE" -ForegroundColor Yellow

if ($status.v3_bridge.available -eq $true) {
    PASS "V3 bridge available"
} else {
    FAIL "V3 bridge available"
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

foreach ($name in $expectedExports) {

    if ($status.v3_bridge.exports -contains $name) {
        PASS "V3 export: $name"
    }
    else {
        FAIL "V3 export: $name"
    }
}

# ------------------------------------------------------------
# 4. CAPABILITY CONTRACT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[4/6] CAPABILITY CONTRACT" -ForegroundColor Yellow

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

    if ($status.capabilities -contains $capability) {
        PASS "capability: $capability"
    }
    else {
        FAIL "capability: $capability"
    }
}

# ------------------------------------------------------------
# 5. MEMORY / PROVIDER / TOOL CONTRACT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[5/6] RUNTIME CONTRACT" -ForegroundColor Yellow

if ($status.memory_persistence -eq "disk") {
    PASS "disk persistence"
} else {
    FAIL "disk persistence"
}

if ($status.memory_scope -eq "owner/profile/session") {
    PASS "memory scope"
} else {
    FAIL "memory scope"
}

if ($status.reasoning_storage -eq "high-level-summary-only") {
    PASS "reasoning storage policy"
} else {
    FAIL "reasoning storage policy"
}

if ($status.providers -contains "owner-mock") {
    PASS "owner provider"
} else {
    FAIL "owner provider"
}

if ($status.tools -contains "echo") {
    PASS "echo tool"
} else {
    FAIL "echo tool"
}

if ($status.tools -contains "summarize") {
    PASS "summarize tool"
} else {
    FAIL "summarize tool"
}

# ------------------------------------------------------------
# 6. SCALE / ORCHESTRATOR CONTRACT
# ------------------------------------------------------------

Write-Host ""
Write-Host "[6/6] ORCHESTRATOR CONTRACT" -ForegroundColor Yellow

if ($status.scale_authority -eq "v3-unified-master-orchestrator") {
    PASS "V3 scale authority"
} else {
    FAIL "V3 scale authority"
}

if ($status.helper_scheduler.activation -eq "bounded-adaptive") {
    PASS "bounded adaptive scheduler"
} else {
    FAIL "bounded adaptive scheduler"
}

if ([int64]$status.helper_scheduler.max_active_workers -eq 128) {
    PASS "worker bound = 128"
} else {
    FAIL "worker bound = 128"
}

if ([int64]$status.helper_scheduler.max_logical_helpers -eq 10000000000) {
    PASS "logical helper bound = 10^10"
} else {
    FAIL "logical helper bound = 10^10"
}

# ------------------------------------------------------------
# FINAL
# ------------------------------------------------------------

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GATE 5 RESULT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "PASSED: $passed" -ForegroundColor Green
Write-Host "FAILED: $failed" -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "GATE 5 - RUNTIME CONTRACT: PASS" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "GATE 5 - RUNTIME CONTRACT: FAIL" -ForegroundColor Red
    exit 1
}
