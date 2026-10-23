@echo off
rem Restart the five detached job queues after a reboot. Double-click it. It starts nothing if the queues already run.
rem The work is done by restart_queues.ps1 (WMI launch, so the queues survive this window and Claude restarts).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0restart_queues.ps1" %*
pause
