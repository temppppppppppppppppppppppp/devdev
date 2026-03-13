$p = Start-Process 'C:\Users\User\Desktop\글도비\geuldobi-desktop\dist\win-unpacked\Geuldobi.exe' -PassThru
Start-Sleep -Seconds 3
$alive = -not $p.HasExited
$exit = if ($p.HasExited) { $p.ExitCode } else { $null }
if ($alive) { Stop-Process -Id $p.Id -Force }
[pscustomobject]@{Pid=$p.Id; AliveAfter3s=$alive; ExitCode=$exit} | Format-List
