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

Push-Location $PSScriptRoot
try {
    & $docker compose --env-file $envFile -f $composeFile down
}
finally {
    Pop-Location
}
