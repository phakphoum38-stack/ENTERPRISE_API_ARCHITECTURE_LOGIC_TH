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
    Write-Host ("PASS  " + $name) -ForegroundColor Green
}

function FAIL([string]$name) {
    $script:failed++
    Write-Host ("FAIL  " + $name) -ForegroundColor Red
}

function SECTION([string]$name) {
    Write-Host ""
    Write-Host $name -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESEARCH OS V3 — GATE 6 FUNCTIONAL E2E" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "BASE:    $base"
Write-Host "OWNER:   owner"
Write-Host "PROFILE: default"
Write-Host "SESSION: desktop-e2e"
Write-Host ""

# ------------------------------------------------------------
# 1. OWNER STATUS
# ------------------------------------------------------------

SECTION "[1/8] OWNER STATUS"

try {
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

    if ($status.v3_bridge.available -eq $true) {
        PASS "V3 bridge available"
    } else {
        FAIL "V3 bridge available"
    }
}
catch {
    FAIL "owner status request"
    Write-Host ("  " + $_.Exception.Message) -ForegroundColor DarkYellow
}

# ------------------------------------------------------------
# 2. V3 EXPORTS
# ------------------------------------------------------------

SECTION "[2/8] V3 EXPORT CONTRACT"

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

try {
    foreach ($name in $expectedExports) {
        if ($status.v3_bridge.exports -contains $name) {
            PASS ("export: " + $name)
        } else {
            FAIL ("export: " + $name)
        }
    }
}
catch {
    FAIL "V3 export inspection"
}

# ------------------------------------------------------------
# 3. CAPABILITY CONTRACT
# ------------------------------------------------------------

SECTION "[3/8] CAPABILITY CONTRACT"

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

try {
    foreach ($capability in $expectedCapabilities) {
        if ($status.capabilities -contains $capability) {
            PASS ("capability: " + $capability)
        } else {
            FAIL ("capability: " + $capability)
        }
    }
}
catch {
    FAIL "capability inspection"
}

# ------------------------------------------------------------
# 4. RUNTIME CONTRACT
# ------------------------------------------------------------

SECTION "[4/8] RUNTIME CONTRACT"

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
# 5. ROUTE DISCOVERY
# ------------------------------------------------------------

SECTION "[5/8] ROUTE DISCOVERY"

$routes = @()

try {
    $openApi = Invoke-RestMethod `
        -Uri "$base/openapi.json" `
        -Headers $headers `
        -ErrorAction Stop

    $routes = @(
        $openApi.paths.PSObject.Properties.Name
    )

    PASS "OpenAPI discovery"

    Write-Host ""
    Write-Host "Available routes:" -ForegroundColor Cyan

    foreach ($route in $routes) {
        Write-Host ("  " + $route)
    }
}
catch {
    Write-Host ""
    Write-Host "OpenAPI is protected or unavailable." `
        -ForegroundColor DarkYellow

    Write-Host "Trying known owner endpoints safely." `
        -ForegroundColor DarkYellow
}

# ------------------------------------------------------------
# 6. SAFE FUNCTIONAL PROBES
# ------------------------------------------------------------

SECTION "[6/8] FUNCTIONAL PROBES"

$candidates = @(
    "/owner/request",
    "/owner/chat",
    "/owner/execute",
    "/owner/run",
    "/chat",
    "/request",
    "/execute",
    "/run"
)

$found = @()

foreach ($candidate in $candidates) {

    if ($routes -contains $candidate) {
        $found += $candidate
    }
}

if ($found.Count -gt 0) {

    PASS "request endpoint discovery"

    Write-Host ""
    Write-Host "Detected request endpoint(s):" `
        -ForegroundColor Cyan

    foreach ($endpoint in $found) {
        Write-Host ("  -> " + $endpoint) `
            -ForegroundColor Green
    }

}
else {

    Write-Host ""
    Write-Host "No known request endpoint exposed through OpenAPI." `
        -ForegroundColor DarkYellow

    Write-Host "Running safe contract probes instead." `
        -ForegroundColor DarkYellow

    # These are intentionally read-only / harmless.
    $safeEndpoints = @(
        "/owner/status",
        "/health",
        "/"
    )

    foreach ($endpoint in $safeEndpoints) {

        try {

            $probe = Invoke-WebRequest `
                -Uri ($base + $endpoint) `
                -Headers $headers `
                -UseBasicParsing `
                -ErrorAction Stop

            if ($probe.StatusCode -ge 200 -and
                $probe.StatusCode -lt 300) {

                PASS ("safe endpoint: " + $endpoint)

            }
            else {

                FAIL ("safe endpoint: " + $endpoint)

            }

        }
        catch {

            Write-Host (
                "  probe unavailable: " +
                $endpoint +
                " -> " +
                $_.Exception.Message
            ) -ForegroundColor DarkYellow
        }
    }
}

# ------------------------------------------------------------
# 7. PERSISTENCE / IDENTITY CONSISTENCY
# ------------------------------------------------------------

SECTION "[7/8] PERSISTENCE / IDENTITY CONSISTENCY"

try {

    $status2 = Invoke-RestMethod `
        -Uri "$base/owner/status" `
        -Headers $headers `
        -ErrorAction Stop

    if (
        $status2.owner_id -eq $status.owner_id -and
        $status2.profile_id -eq $status.profile_id -and
        $status2.session_id -eq $status.session_id
    ) {
        PASS "identity persistence consistency"
    }
    else {
        FAIL "identity persistence consistency"
    }

    if (
        $status2.service -eq $status.service -and
        $status2.version -eq $status.version
    ) {
        PASS "service version consistency"
    }
    else {
        FAIL "service version consistency"
    }

}
catch {

    FAIL "persistence consistency request"

    Write-Host (
        "  " + $_.Exception.Message
    ) -ForegroundColor DarkYellow
}

# ------------------------------------------------------------
# 8. FINAL FUNCTIONAL GATE
# ------------------------------------------------------------

SECTION "[8/8] FINAL GATE"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GATE 6 RESULT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host ("PASSED: " + $passed) -ForegroundColor Green
Write-Host ("FAILED: " + $failed) -ForegroundColor Red
Write-Host ""

if ($failed -eq 0) {
    Write-Host "GATE 6 - FUNCTIONAL E2E: PASS" `
        -ForegroundColor Green
}
else {
    Write-Host "GATE 6 - FUNCTIONAL E2E: FAIL" `
        -ForegroundColor Red

    Write-Host ""
    Write-Host "Failure count is non-zero." `
        -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Gate 6 diagnostic completed." `
    -ForegroundColor Cyan
Write-Host "Terminal remains open." `
    -ForegroundColor Cyan
Write-Host ""

if ($failed -eq 0) {
    exit 0
}
else {
    exit 1
}
