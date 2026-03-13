param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$OutDir = "artifacts/smoke",
    [int]$TimeoutSec = 15,
    [switch]$StopOnFail,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Try-ParseJson {
    param(
        [AllowNull()]
        [string]$Text
    )
    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $null
    }
    try {
        return $Text | ConvertFrom-Json -Depth 100
    } catch {
        return $null
    }
}

function Invoke-SmokeHttp {
    param(
        [string]$Method,
        [string]$Uri,
        [hashtable]$Body,
        [int]$TimeoutSec
    )

    $status = $null
    try {
        if ($null -ne $Body) {
            $jsonBody = $Body | ConvertTo-Json -Depth 50 -Compress
            $response = Invoke-RestMethod -Method $Method -Uri $Uri -ContentType "application/json" -Body $jsonBody -TimeoutSec $TimeoutSec -SkipHttpErrorCheck -StatusCodeVariable status
        } else {
            $response = Invoke-RestMethod -Method $Method -Uri $Uri -TimeoutSec $TimeoutSec -SkipHttpErrorCheck -StatusCodeVariable status
        }

        $raw = $null
        if ($null -ne $response) {
            if ($response -is [string]) {
                $raw = $response
            } else {
                $raw = $response | ConvertTo-Json -Depth 50 -Compress
            }
        }

        $obj = if ($response -is [string]) { Try-ParseJson -Text $response } else { $response }
        return @{
            kind = "http"
            status = [int]$status
            raw = $raw
            body = $obj
        }
    } catch {
        return @{
            kind = "network"
            status = $null
            raw = $_.Exception.Message
            body = $null
        }
    }
}

function Save-Json {
    param(
        [string]$Path,
        [object]$Object
    )
    $json = $Object | ConvertTo-Json -Depth 100
    [System.IO.File]::WriteAllText($Path, $json, $Utf8NoBom)
}

function Append-Jsonl {
    param(
        [string]$Path,
        [object]$Object
    )
    $line = $Object | ConvertTo-Json -Depth 100 -Compress
    [System.IO.File]::AppendAllText($Path, $line + [Environment]::NewLine, $Utf8NoBom)
}

$cases = @(
    @{ id = "SMK-MAIN-001"; method = "POST"; path = "/run"; body = @{ key = "2" }; expectStatus = 202; expectCode = "OK" },
    @{ id = "SMK-K1-001"; method = "POST"; path = "/run"; body = @{ key = "1" }; expectStatus = 202; expectCode = "OK" },
    @{ id = "SMK-K3-001"; method = "POST"; path = "/run"; body = @{ key = "3" }; expectStatus = 202; expectCode = "OK" },
    @{ id = "SMK-K4-001"; method = "POST"; path = "/run"; body = @{ key = "4" }; expectStatus = 202; expectCode = "OK" },
    @{ id = "SMK-K5-001"; method = "POST"; path = "/run"; body = @{ key = "5" }; expectStatus = 202; expectCode = "OK" },
    @{ id = "SMK-K6-001"; method = "POST"; path = "/run"; body = @{ key = "6" }; expectStatus = 202; expectCode = "OK" },
    @{ id = "SMK-P0-001"; method = "POST"; path = "/run"; body = @{ key = "0"; sub_key = "1" }; expectStatus = 202; expectCode = "OK" },
    @{ id = "SMK-P0-002"; method = "POST"; path = "/run"; body = @{ key = "0" }; expectStatus = 400; expectCode = "SUB_KEY_REQUIRED" },
    @{ id = "SMK-P0-003"; method = "POST"; path = "/run"; body = @{ key = "2"; sub_key = "1" }; expectStatus = 400; expectCode = "SUB_KEY_NOT_ALLOWED" },
    @{ id = "SMK-RISK-001"; method = "POST"; path = "/run"; body = @{ key = "44" }; expectStatus = 403; expectCode = "RISK_APPROVAL_REQUIRED" },
    @{ id = "SMK-RISK-002"; method = "POST"; path = "/run"; body = @{ key = "77" }; expectStatus = 403; expectCode = "RISK_APPROVAL_REQUIRED" },
    @{ id = "SMK-RISK-003"; method = "POST"; path = "/run"; body = @{ key = "88" }; expectStatus = 403; expectCode = "RISK_APPROVAL_REQUIRED" },
    @{ id = "SMK-RISK-004"; method = "POST"; path = "/run"; body = @{ key = "99" }; expectStatus = 403; expectCode = "RISK_APPROVAL_REQUIRED" },
    @{ id = "SMK-STOP-001A"; method = "POST"; path = "/stop"; body = $null; expectStatus = 200; expectCode = $null },
    @{ id = "SMK-STOP-001B"; method = "POST"; path = "/stop"; body = $null; expectStatus = 200; expectCode = $null }
)

$startedAt = Get-Date
$resultItems = @()
$passCount = 0
$failCount = 0
$networkCount = 0
$lastFailure = $null

try {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
    $resultJsonlPath = Join-Path $OutDir "smoke-results.jsonl"
    $summaryPath = Join-Path $OutDir "smoke-summary.json"
    $failLogPath = Join-Path $OutDir "smoke-failures.log"

    if (Test-Path $resultJsonlPath) { Remove-Item $resultJsonlPath -Force }
    if (Test-Path $summaryPath) { Remove-Item $summaryPath -Force }
    if (Test-Path $failLogPath) { Remove-Item $failLogPath -Force }

    foreach ($case in $cases) {
        $uri = "{0}{1}" -f $BaseUrl.TrimEnd("/"), $case.path
        $now = Get-Date
        if ($DryRun) {
            $entry = [ordered]@{
                ts = $now.ToString("o")
                id = $case.id
                method = $case.method
                path = $case.path
                dry_run = $true
                pass = $true
                expected = @{
                    status = $case.expectStatus
                    code = $case.expectCode
                }
                actual = @{
                    status = $null
                    code = $null
                }
            }
            $resultItems += $entry
            Append-Jsonl -Path $resultJsonlPath -Object $entry
            $passCount++
            continue
        }

        $http = Invoke-SmokeHttp -Method $case.method -Uri $uri -Body $case.body -TimeoutSec $TimeoutSec
        $actualStatus = $http.status
        $actualCode = $null
        if ($null -ne $http.body) {
            if ($http.body -is [string]) {
                $parsed = Try-ParseJson -Text $http.body
                if ($null -ne $parsed -and $parsed.PSObject.Properties.Name -contains "code") {
                    $actualCode = [string]$parsed.code
                }
            } elseif ($http.body.PSObject.Properties.Name -contains "code") {
                $actualCode = [string]$http.body.code
            }
        }

        $pass = $false
        if ($http.kind -eq "network") {
            $networkCount++
            $pass = $false
        } else {
            $statusOk = ($actualStatus -eq $case.expectStatus)
            $codeOk = ($null -eq $case.expectCode -or $actualCode -eq $case.expectCode)
            $pass = ($statusOk -and $codeOk)
        }

        $entry = [ordered]@{
            ts = $now.ToString("o")
            id = $case.id
            method = $case.method
            path = $case.path
            pass = $pass
            expected = @{
                status = $case.expectStatus
                code = $case.expectCode
            }
            actual = @{
                status = $actualStatus
                code = $actualCode
                kind = $http.kind
            }
            body = $http.body
            raw = $http.raw
        }

        $resultItems += $entry
        Append-Jsonl -Path $resultJsonlPath -Object $entry

        if ($pass) {
            $passCount++
        } else {
            $failCount++
            $lastFailure = $entry
            $line = "FAIL {0}: expected(status={1}, code={2}) actual(status={3}, code={4}, kind={5})" -f `
                $case.id, $case.expectStatus, $case.expectCode, $actualStatus, $actualCode, $http.kind
            [System.IO.File]::AppendAllText($failLogPath, $line + [Environment]::NewLine, $Utf8NoBom)
            Write-Host $line

            if ($StopOnFail) {
                break
            }
        }
    }

    $endedAt = Get-Date
    $summary = [ordered]@{
        started_at = $startedAt.ToString("o")
        ended_at = $endedAt.ToString("o")
        duration_sec = [math]::Round(($endedAt - $startedAt).TotalSeconds, 2)
        base_url = $BaseUrl
        total = $resultItems.Count
        passed = $passCount
        failed = $failCount
        network_errors = $networkCount
        dry_run = [bool]$DryRun
        stop_on_fail = [bool]$StopOnFail
        status = if ($networkCount -gt 0) { "network_error" } elseif ($failCount -gt 0) { "failed" } else { "passed" }
        last_failure = $lastFailure
    }

    Save-Json -Path $summaryPath -Object $summary

    if ($networkCount -gt 0) {
        exit 2
    }
    if ($failCount -gt 0) {
        exit 1
    }
    exit 0
} catch {
    $fallbackPath = Join-Path $OutDir "smoke-failures.log"
    try {
        New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
        [System.IO.File]::AppendAllText($fallbackPath, ("FATAL: " + $_.Exception.Message) + [Environment]::NewLine, $Utf8NoBom)
    } catch {
    }
    Write-Host ("FATAL smoke script error: " + $_.Exception.Message)
    exit 3
}
