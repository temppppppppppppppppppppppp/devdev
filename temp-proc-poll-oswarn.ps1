$matches = @{}
$p = Start-Process 'C:\Users\User\Desktop\글도비\geuldobi-desktop\dist\win-unpacked\Geuldobi.exe' -PassThru
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep -Milliseconds 100
  Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match 'Geuldobi|electron|crashpad|backend|smartscreen|consent|SecurityHealth|OpenWith|WerFault' } | ForEach-Object {
    $key = "$($_.ProcessName)-$($_.Id)"
    if (-not $matches.ContainsKey($key)) {
      $matches[$key] = [pscustomobject]@{SeenAt=(Get-Date); ProcessName=$_.ProcessName; Id=$_.Id; Path=$_.Path; MainWindowTitle=$_.MainWindowTitle }
    }
  }
}
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
if ($matches.Count -eq 0) { 'NO_MATCHED_PROCESSES' } else { $matches.Values | Sort-Object SeenAt | Format-Table -AutoSize }
