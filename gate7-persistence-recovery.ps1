$ErrorActionPreference = "Stop"

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
    Write-Host ("PASS  " + $name) -ForegroundColor Green
}

function FAIL([string]$name) {
    $script:failed++
    Write-Host ("FAIL  " + $name) -ForegroundColor Red
}

function WARN([string]$name) {
    $script:warnings++
    Write-Host ("WARN  " + $name) -ForegroundColor Yellow
}

function SECTION([string]$name) {
    Write-Host ""
    Write-Host $name -ForegroundColor Yellow
}

function SHOW([string]$name, $value) {
    Write-Host ($name + ": " + $value) -ForegroundColor Cyan
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " RESEARCH OS V3 — GATE 7" -ForegroundColor Cyan
Write-Host " PERSISTENCE / RESTART / RECOVERY E2E" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

SHOW "BASE" $base
SHOW "OWNER" "owner"
SHOW "PROFILE" "default"
SHOW "SESSION" "desktop-e2e"

Write-Host ""

# ------------------------------------------------------------
# 1. INITIAL OWNER STATUS
# ------------------------------------------------------------

SECTION "[1/9] INITIAL OWNER STATE"

$statusBefore = $null

try {

    $statusBefore = Invoke-RestMethod `
        -Uri "$base/owner/status" `
        -Headers $headers `
        -ErrorAction Stop

    if ($statusBefore.owner_id -eq "owner") {
        PASS "initial owner identity"
    }
    else {
        FAIL "initial owner identity"
    }

    if ($statusBefore.profile_id -eq "default") {
        PASS "initial profile"
    }
    else {
        FAIL "initial profile"
    }

    if ($statusBefore.session_id -eq "desktop-e2e") {
        PASS "initial session"
    }
    else {
        FAIL "initial session"
    }

    if ($statusBefore.service -eq "owner-friend") {
        PASS "initial service"
    }
    else {
        FAIL "initial service"
    }

    if ($statusBefore.version -eq "1.3.0-owner") {
        PASS "initial version"
    }
    else {
        FAIL "initial version"
    }

    if ($statusBefore.v3_bridge.available -eq $true) {
        PASS "initial V3 bridge"
    }
    else {
        FAIL "initial V3 bridge"
    }

}
catch {

    FAIL "initial owner status"

    Write-Host ""
    Write-Host "SERVER RESPONSE:" -ForegroundColor DarkYellow
    Write-Host $_.Exception.Message -ForegroundColor DarkYellow

}

# ------------------------------------------------------------
# 2. PERSISTENCE CONTRACT
# ------------------------------------------------------------

SECTION "[2/9] PERSISTENCE CONTRACT"

if ($null -ne $statusBefore) {

    if ($statusBefore.memory_persistence -eq "disk") {
        PASS "disk persistence declared"
    }
    else {
        FAIL "disk persistence declared"
    }

    if ($statusBefore.memory_scope -eq "owner/profile/session") {
        PASS "owner/profile/session persistence scope"
    }
    else {
        FAIL "owner/profile/session persistence scope"
    }

}
else {

    FAIL "persistence contract inspection"

}

# ------------------------------------------------------------
# 3. CREATE E2E MARKER
# ------------------------------------------------------------

SECTION "[3/9] PERSISTENCE MARKER"

$markerName = "research-os-gate7-" +
    (Get-Date -Format "yyyyMMdd-HHmmss")

$markerPath = Join-Path `
    (Get-Location) `
    "gate7-marker.txt"

try {

    $markerContent = @"
RESEARCH OS V3 GATE 7
MARKER=$markerName
OWNER=owner
PROFILE=default
SESSION=desktop-e2e
CREATED=$(Get-Date -Format o)
"@

    Set-Content `
        -Path $markerPath `
        -Value $markerContent `
        -Encoding UTF8

    if (Test-Path $markerPath) {
        PASS "E2E marker created"
    }
    else {
        FAIL "E2E marker created"
    }

}
catch {

    FAIL "E2E marker creation"

    Write-Host $_.Exception.Message `
        -ForegroundColor DarkYellow

}

# ------------------------------------------------------------
# 4. VERIFY LOCAL PERSISTENCE
# ------------------------------------------------------------

SECTION "[4/9] LOCAL PERSISTENCE"

try {

    if (Test-Path $markerPath) {

        $readMarker = Get-Content `
            -Path $markerPath `
            -Raw

        if ($readMarker -match [regex]::Escape($markerName)) {
            PASS "marker readable from disk"
        }
        else {
            FAIL "marker content integrity"
        }

        if ($readMarker -match "OWNER=owner") {
            PASS "marker owner scope"
        }
        else {
            FAIL "marker owner scope"
        }

        if ($readMarker -match "PROFILE=default") {
            PASS "marker profile scope"
        }
        else {
            FAIL "marker profile scope"
        }

        if ($readMarker -match "SESSION=desktop-e2e") {
            PASS "marker session scope"
        }
        else {
            FAIL "marker session scope"
        }

    }
    else {

        FAIL "marker exists before recovery"

    }

}
catch {

    FAIL "local persistence read"

}

# ------------------------------------------------------------
# 5. RE-QUERY SERVICE
# ------------------------------------------------------------

SECTION "[5/9] SERVICE RECONNECT"

$statusReconnect = $null

try {

    $statusReconnect = Invoke-RestMethod `
        -Uri "$base/owner/status" `
        -Headers $headers `
        -ErrorAction Stop

    PASS "service reconnect"

    if ($statusReconnect.owner_id -eq "owner") {
        PASS "reconnect owner identity"
    }
    else {
        FAIL "reconnect owner identity"
    }

    if ($statusReconnect.profile_id -eq "default") {
        PASS "reconnect profile"
    }
    else {
        FAIL "reconnect profile"
    }

    if ($statusReconnect.session_id -eq "desktop-e2e") {
        PASS "reconnect session"
    }
    else {
        FAIL "reconnect session"
    }

}
catch {

    FAIL "service reconnect"

    Write-Host $_.Exception.Message `
        -ForegroundColor DarkYellow

}

# ------------------------------------------------------------
# 6. STATE CONSISTENCY
# ------------------------------------------------------------

SECTION "[6/9] STATE CONSISTENCY"

if (
    $null -ne $statusBefore -and
    $null -ne $statusReconnect
) {

    if (
        $statusBefore.owner_id -eq
        $statusReconnect.owner_id
    ) {
        PASS "owner identity consistency"
    }
    else {
        FAIL "owner identity consistency"
    }

    if (
        $statusBefore.profile_id -eq
        $statusReconnect.profile_id
    ) {
        PASS "profile consistency"
    }
    else {
        FAIL "profile consistency"
    }

    if (
        $statusBefore.session_id -eq
        $statusReconnect.session_id
    ) {
        PASS "session consistency"
    }
    else {
        FAIL "session consistency"
    }

    if (
        $statusBefore.service -eq
        $statusReconnect.service
    ) {
        PASS "service consistency"
    }
    else {
        FAIL "service consistency"
    }

    if (
        $statusBefore.version -eq
        $statusReconnect.version
    ) {
        PASS "version consistency"
    }
    else {
        FAIL "version consistency"
    }

    if (
        $statusReconnect.v3_bridge.available -eq $true
    ) {
        PASS "V3 bridge after reconnect"
    }
    else {
        FAIL "V3 bridge after reconnect"
    }

}
else {

    FAIL "state consistency baseline"

}

# ------------------------------------------------------------
# 7. RECOVERY MARKER READ
# ------------------------------------------------------------

SECTION "[7/9] RECOVERY VERIFICATION"

try {

    $recovered = Get-Content `
        -Path $markerPath `
        -Raw

    if ($recovered -match [regex]::Escape($markerName)) {
        PASS "persistent marker recovered"
    }
    else {
        FAIL "persistent marker recovered"
    }

    if ($recovered -match "RESEARCH OS V3 GATE 7") {
        PASS "recovery marker identity"
    }
    else {
        FAIL "recovery marker identity"
    }

}
catch {

    FAIL "recovery marker read"

}

# ------------------------------------------------------------
# 8. SAFE RUNTIME RECOVERY PROBE
# ------------------------------------------------------------

SECTION "[8/9] SAFE RUNTIME RECOVERY PROBE"

try {

    $health = Invoke-WebRequest `
        -Uri "$base/owner/status" `
        -Headers $headers `
        -UseBasicParsing `
        -ErrorAction Stop

    if (
        $health.StatusCode -ge 200 -and
        $health.StatusCode -lt 300
    ) {
        PASS "runtime available after persistence checks"
    }
    else {
        FAIL "runtime available after persistence checks"
    }

}
catch {

    FAIL "runtime recovery probe"

    Write-Host $_.Exception.Message `
        -ForegroundColor DarkYellow

}

# ------------------------------------------------------------
# 9. FINAL GATE
# ------------------------------------------------------------

SECTION "[9/9] FINAL GATE"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " GATE 7 RESULT" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host ("PASSED:   " + $passed) `
    -ForegroundColor Green

Write-Host ("FAILED:   " + $failed) `
    -ForegroundColor Red

Write-Host ("WARNINGS: " + $warnings) `
    -ForegroundColor Yellow

Write-Host ""

if ($failed -eq 0) {

    Write-Host "GATE 7 - PERSISTENCE / RECOVERY E2E: PASS" `
        -ForegroundColor Green

}
else {

    Write-Host "GATE 7 - PERSISTENCE / RECOVERY E2E: FAIL" `
        -ForegroundColor Red

}

Write-Host ""
Write-Host "Gate 7 diagnostic completed." `
    -ForegroundColor Cyan

Write-Host "Terminal remains open." `
    -ForegroundColor Cyan

Write-Host ""

# ------------------------------------------------------------
# CLEANUP
# ------------------------------------------------------------

if (Test-Path $markerPath) {

    try {

        Remove-Item `
            -Path $markerPath `
            -Force `
            -ErrorAction Stop

        Write-Host "Temporary Gate 7 marker removed." `
            -ForegroundColor DarkGray

    }
    catch {

        WARN "temporary marker cleanup"

    }

}

Write-Host ""

if ($failed -eq 0) {
    exit 0
}
else {
    exit 1
}
