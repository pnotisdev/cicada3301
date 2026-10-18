@echo off
rem h5rs flat-library campaign launcher (see work/h5rs/CAMPAIGN.md).
rem Run from the repo root, detached:  Start-Process -FilePath cmd.exe -ArgumentList '/c','work\h5rs\launch_campaign.bat' -WindowStyle Hidden
rem NOT resumable: a kill leaves the partial TSV and a restart begins from ZERO
rem (both outputs are recreated). Kill: taskkill /F /T /PID <pid>  or  taskkill /F /IM h5rs.exe
setlocal
cd /d "%~dp0..\.."
set BIN=work\h5rs\target\release\h5rs.exe
set WIN=work\h5rs\data\lp2_windows.txt

echo == h5rs flat-library campaign start %date% %time% == > results\h5rs_flat_sweep.log
echo == h5rs flat-library campaign start %date% %time% == > results\h5rs_flat_null.log

rem 1) real sweep: 581 library streams x 8 windows x 2000 offsets x 19 L x 2 models
%windir%\System32\where.exe %BIN% >nul 2>nul
if errorlevel 1 (
  echo ERROR: %BIN% not found - build it first: cargo build --release in work\h5rs >> results\h5rs_flat_sweep.log
  exit /b 1
)
%BIN% sweep %WIN% file:work\kscreen\data\library_flat.ksb 0 2000 2 20 2 8 results\h5rs_flat_sweep.tsv --hits 1.5 --chunk 10 --progress 1 >> results\h5rs_flat_sweep.log 2>&1
echo real sweep exit code %ERRORLEVEL% at %date% %time% >> results\h5rs_flat_sweep.log

rem 2) matched-null sweep: 8 replicates (seeds 9000..9007) over the same grid
%BIN% sweep %WIN% file:work\h5rs\data\null8.ksb 0 2000 2 20 2 8 results\h5rs_flat_null.tsv --hits 1.5 --chunk 10 --progress 1 --best >> results\h5rs_flat_null.log 2>&1
echo null sweep exit code %ERRORLEVEL% at %date% %time% >> results\h5rs_flat_null.log
echo == campaign job finished %date% %time% == >> results\h5rs_flat_null.log
