<#
.SYNOPSIS
    Geuldobi desktop release build for the source_bundle_primary runtime.

.DESCRIPTION
    1. Prepare the embedded Python runtime.
    2. Build backend.exe with PyInstaller.
    3. Stage the engine source bundle into dist/engine.
    4. Stage the workspace seed and verify the staged resource inventory.
    5. Build the Electron installer and verify the packaged resource inventory.

.USAGE
    cd build
    powershell -ExecutionPolicy Bypass -File build_release.ps1

.NOTES
    Prerequisites:
    - Python 3.11+
    - pip install pyinstaller google-genai pydantic pyyaml numpy httpx
    - Node.js 18+
    - cd geuldobi-desktop && npm install
#>

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = Split-Path $PSScriptRoot -Parent
$BUILD_DIR = $PSScriptRoot
$DIST_DIR = Join-Path $PROJECT_ROOT "dist"
$DESKTOP_DIR = Join-Path $PROJECT_ROOT "geuldobi-desktop"
$DESKTOP_DIST_DIR = Join-Path $DESKTOP_DIR "dist"
$RUNTIME_CONTRACT = "source_bundle_primary"
$STAGING_RESOURCE_INVENTORY = @(
    "dist\backend\backend.exe",
    "dist\engine\main_a.py",
    "python-embed\python.exe",
    "dist\workspace-seed\seed-manifest.json"
)
$PACKAGED_RESOURCE_INVENTORY = @(
    "backend\backend.exe",
    "engine\main_a.py",
    "python-embed\python.exe",
    "workspace-seed\seed-manifest.json"
)

function Reset-Directory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (Test-Path $Path) {
        Remove-Item -Recurse -Force $Path
    }
    New-Item -ItemType Directory -Path $Path | Out-Null
}

function Copy-BundleItem {
    param(
        [Parameter(Mandatory = $true)]
        [string]$SourceRelativePath,
        [Parameter(Mandatory = $true)]
        [string]$DestinationRoot
    )

    $sourcePath = Join-Path $PROJECT_ROOT $SourceRelativePath
    if (-not (Test-Path $sourcePath)) {
        throw "Source bundle path missing: $sourcePath"
    }

    $destinationPath = Join-Path $DestinationRoot $SourceRelativePath
    New-Item -ItemType Directory -Path (Split-Path $destinationPath -Parent) -Force | Out-Null
    Copy-Item -Path $sourcePath -Destination $destinationPath -Recurse -Force
}

function Sync-EngineBundle {
    $engineDistDir = Join-Path $DIST_DIR "engine"
    $bundleItems = @(
        "main_a.py",
        "modules",
        "config",
        "datasets",
        "libraries",
        "lite_mode"
    )

    Write-Host "[sync] staging engine source bundle ..."
    Reset-Directory $engineDistDir
    foreach ($relativePath in $bundleItems) {
        Copy-BundleItem -SourceRelativePath $relativePath -DestinationRoot $engineDistDir
    }
}

function Assert-PackagedResources {
    param(
        [Parameter(Mandatory = $true)]
        [string]$BasePath,
        [Parameter(Mandatory = $true)]
        [string[]]$Inventory,
        [Parameter(Mandatory = $true)]
        [string]$Label
    )

    foreach ($resource in $Inventory) {
        $candidate = Join-Path $BasePath $resource
        if (-not (Test-Path $candidate)) {
            throw "$Label resource missing: $candidate"
        }
    }
    Write-Host "[verify] $Label resources OK"
}

Write-Host "================================================"
Write-Host "  Geuldobi Desktop Release Build"
Write-Host "================================================"
Write-Host "runtime contract: $RUNTIME_CONTRACT"
Write-Host ""

Write-Host "[Step 1/4] Preparing embedded Python ..."
& powershell -ExecutionPolicy Bypass -File (Join-Path $BUILD_DIR "prepare_python_embed.ps1")
if ($LASTEXITCODE -ne 0) {
    throw "prepare_python_embed.ps1 failed"
}
Write-Host ""

Write-Host "[Step 2/4] Building backend.exe with PyInstaller ..."
Reset-Directory (Join-Path $DIST_DIR "backend")
Push-Location $BUILD_DIR
try {
    & python -m PyInstaller backend.spec --distpath $DIST_DIR --clean -y
    if ($LASTEXITCODE -ne 0) {
        throw "backend.exe PyInstaller build failed"
    }
} finally {
    Pop-Location
}
Write-Host ""

Write-Host "[Step 3/4] Staging source bundle + workspace seed ..."
Sync-EngineBundle
& python (Join-Path $DESKTOP_DIR "scripts\build_workspace_seed.py")
if ($LASTEXITCODE -ne 0) {
    throw "workspace seed staging failed"
}
Assert-PackagedResources -BasePath $PROJECT_ROOT -Inventory $STAGING_RESOURCE_INVENTORY -Label "staging"
Write-Host ""

Write-Host "[Step 4/4] Building Electron installer ..."
Push-Location $DESKTOP_DIR
try {
    & npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "Electron Builder failed"
    }
} finally {
    Pop-Location
}

$PACKAGED_RESOURCES_ROOT = Join-Path $DESKTOP_DIST_DIR "win-unpacked\resources"
Assert-PackagedResources -BasePath $PACKAGED_RESOURCES_ROOT -Inventory $PACKAGED_RESOURCE_INVENTORY -Label "packaged"

Write-Host ""
Write-Host "================================================"
Write-Host "  Build Complete"
Write-Host "================================================"
Write-Host ""
Write-Host "Installer location:"
Get-ChildItem -Path $DESKTOP_DIST_DIR -Filter "*.exe" | ForEach-Object {
    Write-Host "  $($_.FullName)  ($([math]::Round($_.Length / 1MB, 1)) MB)"
}
