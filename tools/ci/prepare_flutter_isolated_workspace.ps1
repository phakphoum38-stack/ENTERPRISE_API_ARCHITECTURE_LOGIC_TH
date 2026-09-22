[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryRoot,

    [Parameter(Mandatory = $true)]
    [string]$AppRelativePath,

    [Parameter(Mandatory = $true)]
    [string]$WorkspaceRoot
)

$ErrorActionPreference = 'Stop'

function Get-RepoRelativePath {
    param([string]$Path)

    $full = [System.IO.Path]::GetFullPath($Path)
    $repo = [System.IO.Path]::GetFullPath($RepositoryRoot).TrimEnd('\') + '\'

    if (-not $full.StartsWith($repo, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path '$full' is outside repository root '$RepositoryRoot'."
    }

    return $full.Substring($repo.Length).Replace('\', '/')
}

function Get-LocalPathDependencies {
    param([string]$PubspecPath)

    $lines = Get-Content -LiteralPath $PubspecPath
    $section = $null
    $sectionIndent = -1
    $currentDependencyIndent = -1
    $currentDependency = $null
    $results = @()

    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith('#')) { continue }

        $indent = $line.Length - $line.TrimStart().Length
        $trimmed = $line.Trim()

        if ($indent -eq 0 -and ($trimmed -eq 'dependencies:' -or $trimmed -eq 'dev_dependencies:' -or $trimmed -eq 'dependency_overrides:')) {
            $section = $trimmed.Substring(0, $trimmed.Length - 1)
            $sectionIndent = $indent
            $currentDependency = $null
            continue
        }

        if ($indent -eq 0 -and $trimmed.Contains(':')) {
            $section = $null
            $currentDependency = $null
            continue
        }

        if ($null -eq $section) { continue }

        if ($currentDependency -ne $null -and $indent -eq $currentDependencyIndent -and $trimmed.EndsWith(':')) {
            $currentDependency = $trimmed.Substring(0, $trimmed.Length - 1)
            $currentDependencyIndent = $indent
            continue
        }

        if ($currentDependency -eq $null -and $trimmed.EndsWith(':')) {
            $currentDependency = $trimmed.Substring(0, $trimmed.Length - 1)
            $currentDependencyIndent = $indent
            continue
        }

        if ($currentDependency -ne $null -and $indent -gt $currentDependencyIndent -and $trimmed.StartsWith('path:')) {
            $value = $trimmed.Substring(5).Trim().Trim('"').Trim("'")
            if ([string]::IsNullOrWhiteSpace($value)) {
                throw "Empty local path dependency in '$PubspecPath'."
            }
            $results += [PSCustomObject]@{
                Name = $currentDependency
                Path = $value
            }
            $currentDependency = $null
            continue
        }

        if ($currentDependency -ne $null -and $indent -le $currentDependencyIndent) {
            $currentDependency = $null
        }
    }

    return $results
}

if (-not (Test-Path -LiteralPath $RepositoryRoot -PathType Container)) {
    throw "Repository root does not exist: $RepositoryRoot"
}

$appSource = Join-Path $RepositoryRoot $AppRelativePath
$appPubspec = Join-Path $appSource 'pubspec.yaml'
if (-not (Test-Path -LiteralPath $appPubspec -PathType Leaf)) {
    throw "Application pubspec.yaml is missing: $appPubspec"
}

if (Test-Path -LiteralPath $WorkspaceRoot) {
    Remove-Item -LiteralPath $WorkspaceRoot -Recurse -Force
}

New-Item -ItemType Directory -Path $WorkspaceRoot -Force | Out-Null

$queue = New-Object System.Collections.Generic.Queue[string]
$visited = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)
$queue.Enqueue([System.IO.Path]::GetFullPath($appSource))

while ($queue.Count -gt 0) {
    $source = $queue.Dequeue()
    $sourceFull = [System.IO.Path]::GetFullPath($source)

    if (-not $visited.Add($sourceFull)) { continue }

    $relative = Get-RepoRelativePath -Path $sourceFull
    $target = Join-Path $WorkspaceRoot ($relative.Replace('/', '\'))

    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Get-ChildItem -LiteralPath $sourceFull -Force | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $target -Recurse -Force
    }

    $pubspec = Join-Path $sourceFull 'pubspec.yaml'
    if (-not (Test-Path -LiteralPath $pubspec -PathType Leaf)) { continue }

    foreach ($dependency in Get-LocalPathDependencies -PubspecPath $pubspec) {
        $dependencySource = [System.IO.Path]::GetFullPath((Join-Path $sourceFull $dependency.Path))
        if (-not (Test-Path -LiteralPath $dependencySource -PathType Container)) {
            throw "Local path dependency '$($dependency.Name)' does not exist: $dependencySource"
        }

        $dependencyRelative = Get-RepoRelativePath -Path $dependencySource
        Write-Host "RESEARCH_OS_ISOLATED_PATH_DEPENDENCY=$dependencyRelative"
        $queue.Enqueue($dependencySource)
    }
}

$appTarget = Join-Path $WorkspaceRoot ($AppRelativePath.Replace('/', '\'))
if (-not (Test-Path -LiteralPath (Join-Path $appTarget 'pubspec.yaml') -PathType Leaf)) {
    throw "Isolated application pubspec.yaml is missing: $appTarget"
}

Write-Host "RESEARCH_OS_ISOLATED_WORKSPACE=PASS"
Write-Host "RESEARCH_OS_ISOLATED_APP=$appTarget"
