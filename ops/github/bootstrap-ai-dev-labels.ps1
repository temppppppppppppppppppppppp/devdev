$ErrorActionPreference = "Stop"

param(
    [string]$Repo,
    [string]$LabelSpecPath = "",
    [switch]$UpdateExisting
)

function Resolve-RepoFromOrigin {
    $remote = git remote get-url origin 2>$null
    if (-not $remote) {
        throw "Could not resolve origin remote. Pass -Repo owner/name explicitly."
    }

    if ($remote -match 'github\.com[:/](?<repo>[^/]+/[^/.]+)(?:\.git)?$') {
        return $Matches.repo
    }

    throw "Origin remote is not a GitHub owner/name URL: $remote"
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Push-Location $repoRoot
try {
    if (-not $Repo) {
        $Repo = Resolve-RepoFromOrigin
    }

    if (-not $LabelSpecPath) {
        $LabelSpecPath = Join-Path $PSScriptRoot "ai-dev-labels.json"
    }

    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        throw "GitHub CLI 'gh' is required to apply labels."
    }

    $labels = Get-Content -LiteralPath $LabelSpecPath -Encoding UTF8 -Raw | ConvertFrom-Json
    foreach ($label in $labels) {
        & gh label create $label.name --repo $Repo --color $label.color --description $label.description 2>$null
        if ($LASTEXITCODE -ne 0) {
            if ($UpdateExisting) {
                & gh label edit $label.name --repo $Repo --color $label.color --description $label.description
            }
            else {
                Write-Output "Skipped existing label: $($label.name)"
            }
        }
        else {
            Write-Output "Created label: $($label.name)"
        }
    }
}
finally {
    Pop-Location
}
