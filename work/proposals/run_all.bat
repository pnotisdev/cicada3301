@echo off
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
for /d %%d in (*) do (
  if exist "%%d\run.bat" (
    echo.
    echo ==================== %%d ====================
    call "%%d\run.bat"
  )
)
