$ErrorActionPreference = "Stop"

$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
$dockerBin = "C:\Program Files\Docker\Docker\resources\bin"
if (-not (Test-Path -LiteralPath $docker)) {
    $docker = "docker"
}
elseif (-not ($env:PATH -split ";" | Where-Object { $_ -eq $dockerBin })) {
    $env:PATH = "$dockerBin;$env:PATH"
}

$envFile = Join-Path $PSScriptRoot "..\..\secrets\n8n.local.env"
$composeFile = Join-Path $PSScriptRoot "docker-compose.yml"
$localFiles = Join-Path $PSScriptRoot "local-files"

if (-not (Test-Path -LiteralPath $envFile)) {
    throw "Missing env file: $envFile"
}

if (-not (Test-Path -LiteralPath $localFiles)) {
    New-Item -ItemType Directory -Path $localFiles | Out-Null
}

Push-Location $PSScriptRoot
try {
    & $docker compose --env-file $envFile -f $composeFile up -d
}
finally {
    Pop-Location
}
