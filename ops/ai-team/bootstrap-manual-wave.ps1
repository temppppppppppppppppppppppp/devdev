param(
    [Parameter(Mandatory = $true)]
    [string]$IssueId,
    [string]$BaseBranch = "main",
    [string]$WorktreeParent = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Test-BranchExists {
    param([string]$BranchName)
    git show-ref --verify --quiet ("refs/heads/" + $BranchName)
    return $LASTEXITCODE -eq 0
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
if (-not $WorktreeParent) {
    $WorktreeParent = Split-Path $repoRoot -Parent
}

$integrationBranch = "integration/$IssueId"
$workerABranch = "task/$IssueId-a"
$workerBBranch = "task/$IssueId-b"

$integrationPath = Join-Path $WorktreeParent "wt-$IssueId-int"
$workerAPath = Join-Path $WorktreeParent "wt-$IssueId-a"
$workerBPath = Join-Path $WorktreeParent "wt-$IssueId-b"

Push-Location $repoRoot
try {
    git rev-parse --verify $BaseBranch | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Base branch '$BaseBranch' does not exist."
    }

    foreach ($branch in @($integrationBranch, $workerABranch, $workerBBranch)) {
        if (Test-BranchExists -BranchName $branch) {
            throw "Branch already exists: $branch"
        }
    }

    foreach ($path in @($integrationPath, $workerAPath, $workerBPath)) {
        if (Test-Path -LiteralPath $path) {
            throw "Worktree path already exists: $path"
        }
    }

    if ($DryRun) {
        Write-Output "Dry run only. No branches or worktrees were created."
        Write-Output "  git worktree add $integrationPath -b $integrationBranch $BaseBranch"
        Write-Output "  git worktree add $workerAPath -b $workerABranch $BaseBranch"
        Write-Output "  git worktree add $workerBPath -b $workerBBranch $BaseBranch"
        return
    }

    git worktree add $integrationPath -b $integrationBranch $BaseBranch
    git worktree add $workerAPath -b $workerABranch $BaseBranch
    git worktree add $workerBPath -b $workerBBranch $BaseBranch

    Write-Output "Created manual wave:"
    Write-Output "  integration branch: $integrationBranch"
    Write-Output "  integration path:   $integrationPath"
    Write-Output "  worker A branch:    $workerABranch"
    Write-Output "  worker A path:      $workerAPath"
    Write-Output "  worker B branch:    $workerBBranch"
    Write-Output "  worker B path:      $workerBPath"
}
finally {
    Pop-Location
}
