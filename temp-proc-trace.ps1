Register-WmiEvent -Class Win32_ProcessStartTrace -SourceIdentifier geuldobiStart | Out-Null
$events = @()
$p = Start-Process 'C:\Users\User\Desktop\글도비\geuldobi-desktop\dist\win-unpacked\Geuldobi.exe' -PassThru
$deadline = (Get-Date).AddSeconds(5)
while ((Get-Date) -lt $deadline) {
  $evt = Wait-Event -SourceIdentifier geuldobiStart -Timeout 1
  if ($evt) {
    $proc = $evt.SourceEventArgs.NewEvent
    if ($proc.ProcessName -match 'Geuldobi|electron|crashpad|backend') {
      $events += [pscustomobject]@{Time=Get-Date; ProcessName=$proc.ProcessName; ProcessId=$proc.ProcessId; ParentProcessId=$proc.ParentProcessId; Sid=$proc.SID }
    }
    Remove-Event -EventIdentifier $evt.EventIdentifier | Out-Null
  }
}
Unregister-Event -SourceIdentifier geuldobiStart -ErrorAction SilentlyContinue
Get-Job | Remove-Job -Force -ErrorAction SilentlyContinue
if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force }
if ($events.Count -eq 0) { 'NO_MATCHED_PROCESSES' } else { $events | Format-Table -AutoSize }
