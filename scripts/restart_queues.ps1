# Restart the five detached job queues after a reboot (docs/QUEUE.md); called by restart_queues.bat.
# Each queue is started through WMI, so closing the window or restarting the Claude app does not stop it.
# Every job is resumable (finished outputs are skipped). -DryRun prints the command lines without starting anything.
param([switch]$DryRun)
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$conda = (Get-Command python -ErrorAction Stop).Source          # booknight runs on the miniconda python on PATH
$venv = Join-Path $root ".venv\Scripts\python.exe"
$kb = Join-Path $root "work\kscreen\target\pdir\kscreen.exe"
foreach ($f in $venv, $kb) { if (-not (Test-Path $f)) { Write-Host "missing: $f"; exit 1 } }
$running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'jobqueue\.py' }
if ($running -and -not $DryRun) { Write-Host "Queues are already running ($($running.Count) processes); nothing started."; exit 0 }

$w = 'cmd /c set QUEUE_MAX_WAIT_SECONDS=172800&& '
$cmds = @(
    "`"$conda`" jobs\jobqueue.py booknight jobs\queues\booknight.txt",
    ($w + "set `"KSCREEN_BIN=$kb`"&& `"$venv`" jobs\jobqueue.py pdir jobs\queues\pdir.txt"),
    ($w + "`"$venv`" jobs\jobqueue.py layout jobs\queues\layout.txt"),
    ($w + "`"$venv`" jobs\jobqueue.py wordjump jobs\queues\wordjump.txt"),
    ($w + "`"$venv`" jobs\jobqueue.py r4lib jobs\queues\r4lib.txt"))
foreach ($c in $cmds) {
    $name = ($c -split 'jobqueue.py ')[1].Split(' ')[0]
    if ($DryRun) { Write-Host "would start $name"; continue }
    $r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $c; CurrentDirectory = $root }
    Write-Host "started $name (rc $($r.ReturnValue))"
    Start-Sleep -Seconds 20                                      # booknight first: the others wait for it
}
if (-not $DryRun) {
    Write-Host "Waiting 60 s, then lowering the queues' priority..."
    Start-Sleep -Seconds 60
    & $conda scripts\queue_priority.py
    Write-Host "Done. Progress: results\overnight\desktop\queue\booknight__kjv.log"
}
