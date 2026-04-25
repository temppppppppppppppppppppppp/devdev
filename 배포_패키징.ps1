# 글도비 배포용 ZIP 생성 스크립트
# 실행: PowerShell에서 .\배포_패키징.ps1

$source = Split-Path -Parent $MyInvocation.MyCommand.Path
$output = "C:\gldobi_deploy.zip"

# 제외할 폴더/파일 목록
$exclude = @(
    ".git",
    ".claude",
    ".pytest_cache",
    ".ruff_cache",
    ".hypothesis",
    ".github",
    ".venv",
    "venv",
    "__pycache__",
    "projects",
    "logs",
    "백업",
    "lite_mode",
    "spikes",
    "MagicMock",
    "tmp_stage2_digest_debug",
    "test_mode",
    "rlhf_data",
    "datasets",
    "main_tools",
    "tools",
    "tools2",
    "scripts"
)

# 제외할 파일
$excludeFiles = @(
    ".env",
    "CLAUDE.md",
    "crash_dump.log",
    "error.log",
    "test_results.xml",
    "nu_",
    "nul",
    "배포_패키징.ps1"
)

Write-Host "배포용 ZIP 생성 중..." -ForegroundColor Cyan
Write-Host "출력 위치: $output" -ForegroundColor Gray

if (Test-Path $output) {
    Remove-Item $output -Force
}

# 포함할 파일 수집
$files = Get-ChildItem -Path $source -Recurse | Where-Object {
    $item = $_
    $relativePath = $item.FullName.Substring($source.Length + 1)
    $topLevel = $relativePath.Split([IO.Path]::DirectorySeparatorChar)[0]

    # 폴더 제외
    if ($exclude -contains $topLevel) { return $false }
    if ($exclude -contains $item.Name) { return $false }

    # __pycache__ 하위 제외
    if ($relativePath -match "__pycache__") { return $false }

    # 파일 제외
    if ($item.PSIsContainer -eq $false) {
        if ($excludeFiles -contains $item.Name) { return $false }
        if ($item.Extension -eq ".pyc") { return $false }
        if ($item.Extension -eq ".db") { return $false }
        if ($item.Extension -eq ".db-shm") { return $false }
        if ($item.Extension -eq ".db-wal") { return $false }
    }

    return $true
}

# ZIP 생성
$tempDir = "C:\gldobipack_temp"
if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -ItemType Directory -Path $tempDir | Out-Null

foreach ($file in $files) {
    if ($file.PSIsContainer) { continue }
    $relativePath = $file.FullName.Substring($source.Length + 1)
    $destPath = Join-Path $tempDir $relativePath
    $destDir = Split-Path $destPath -Parent
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    Copy-Item $file.FullName -Destination $destPath
}

Compress-Archive -Path "$tempDir\*" -DestinationPath $output -CompressionLevel Optimal
Remove-Item $tempDir -Recurse -Force -ErrorAction SilentlyContinue

$size = [math]::Round((Get-Item $output).Length / 1MB, 1)
Write-Host "완료! 파일 크기: ${size}MB" -ForegroundColor Green
Write-Host "위치: $output" -ForegroundColor Green
