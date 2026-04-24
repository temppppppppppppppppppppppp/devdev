<#
.SYNOPSIS
    내장 Python (embeddable) 다운로드 + pip 설치 + 런타임 패키지 설치.

.DESCRIPTION
    python-3.12.x-embed-amd64.zip 을 다운받아 ../python-embed/ 에 풀고,
    pip를 활성화한 뒤 main_a.py 실행에 필요한 런타임 패키지만 설치한다.
    (FastAPI/uvicorn은 PyInstaller backend.exe에 포함되므로 여기선 불필요)

.USAGE
    cd build
    powershell -ExecutionPolicy Bypass -File prepare_python_embed.ps1
#>

$ErrorActionPreference = "Stop"

$PY_VERSION = "3.12.8"
$PY_ZIP = "python-${PY_VERSION}-embed-amd64.zip"
$PY_URL = "https://www.python.org/ftp/python/${PY_VERSION}/${PY_ZIP}"
$GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

$EMBED_DIR = Join-Path (Split-Path $PSScriptRoot -Parent) "python-embed"
$CACHE_DIR = Join-Path $PSScriptRoot ".cache"

# ── 1. 다운로드 (캐시) ───────────────────────────────────────────────────────

if (-not (Test-Path $CACHE_DIR)) { New-Item -ItemType Directory -Path $CACHE_DIR | Out-Null }

$zipPath = Join-Path $CACHE_DIR $PY_ZIP
if (-not (Test-Path $zipPath)) {
    Write-Host "[1/5] Downloading $PY_ZIP ..."
    Invoke-WebRequest -Uri $PY_URL -OutFile $zipPath -UseBasicParsing
} else {
    Write-Host "[1/5] Using cached $PY_ZIP"
}

# ── 2. 압축 해제 ─────────────────────────────────────────────────────────────

if (Test-Path $EMBED_DIR) { Remove-Item -Recurse -Force $EMBED_DIR }
Write-Host "[2/5] Extracting to $EMBED_DIR ..."
Expand-Archive -Path $zipPath -DestinationPath $EMBED_DIR

# ── 3. pip 활성화 (._pth 파일에서 import site 주석 해제) ─────────────────────

$pthFile = Get-ChildItem -Path $EMBED_DIR -Filter "python*._pth" | Select-Object -First 1
if ($pthFile) {
    Write-Host "[3/5] Enabling pip (uncommenting 'import site' in $($pthFile.Name)) ..."
    $content = Get-Content $pthFile.FullName
    $content = $content -replace "^#\s*import site", "import site"
    Set-Content $pthFile.FullName $content
} else {
    Write-Warning "._pth file not found — pip may not work"
}

# ── 4. pip 설치 ───────────────────────────────────────────────────────────────

$getPipPath = Join-Path $CACHE_DIR "get-pip.py"
if (-not (Test-Path $getPipPath)) {
    Write-Host "[4/5] Downloading get-pip.py ..."
    Invoke-WebRequest -Uri $GET_PIP_URL -OutFile $getPipPath -UseBasicParsing
} else {
    Write-Host "[4/5] Using cached get-pip.py"
}

$pythonExe = Join-Path $EMBED_DIR "python.exe"
& $pythonExe $getPipPath --no-warn-script-location
if ($LASTEXITCODE -ne 0) {
    throw "get-pip.py failed"
}

# ── 5. 런타임 패키지 설치 ────────────────────────────────────────────────────

Write-Host "[5/5] Installing runtime packages ..."

& $pythonExe -m pip install --no-cache-dir --no-warn-script-location `
    "google-genai>=1.60.0" `
    "rich>=13.0" `
    "python-dotenv>=1.0" `
    "numpy>=1.26" `
    "requests>=2.31" `
    "beautifulsoup4>=4.12" `
    "sqlite-vec>=0.1.6" `
    "pydantic>=2.0" `
    "pyyaml>=6.0" `
    "nest-asyncio>=1.5"
if ($LASTEXITCODE -ne 0) {
    throw "embedded runtime package install failed"
}

Write-Host ""
Write-Host "=== Done ==="
Write-Host "Embedded Python: $pythonExe"
$size = (Get-ChildItem -Path $EMBED_DIR -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "Total size: $([math]::Round($size, 1)) MB"
