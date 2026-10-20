@echo off
rem h5rs flat-library campaign launcher, block-resumable (see work/h5rs/CAMPAIGN.md).
rem Run from the repo root, detached:
rem   Start-Process -FilePath cmd.exe -ArgumentList '/c','work\h5rs\launch_campaign_blocks.bat' -WindowStyle Hidden
rem
rem 5 REAL blocks of 400 offsets (0-399, 400-799, 800-1199, 1200-1599, 1600-1999), each
rem writing work\tmp\h5rs_blocktest\bat_block<N>.tsv + .log, then the matched-null sweep
rem (null8.ksb) -> work\tmp\h5rs_blocktest\bat_null.tsv + .log.
rem
rem RESUME: a block is finished when its work\tmp\h5rs_blocktest\bat_block<N>.done marker exists;
rem a kill/reboot restarts only the current block (its partial .tsv/.log are recreated)
rem and finished blocks are kept. After all 5 blocks complete, merge manually:
rem   python work\h5rs\merge_blocks.py results\h5rs_flat_sweep.tsv ^
rem        work\tmp\h5rs_blocktest\bat_block1.tsv ... work\tmp\h5rs_blocktest\bat_block5.tsv
rem
rem Kill: taskkill /F /T /PID <pid of the launched cmd>  or  taskkill /F /IM h5rs.exe
rem (killing the engine makes the bat finish the current block as FAILED and stop).
rem NOTE: no parentheses or semicolons inside parenthesized blocks (batch parse hazards);
rem the control flow is goto-style on purpose.
setlocal
cd /d "%~dp0..\..\.."
set BIN=work\h5rs\target\release\h5rs.exe
set WIN=work\h5rs\data\lp2_windows.txt
set LIB=work\h5rs\data\null2.ksb
rem The matched-null sweep below uses null8.ksb (8 replicates). The pre-launch null-size
rem measurement (CAMPAIGN.md) shows the campaign-scale (581-stream) null max exceeds the
rem 8-stream max by +0.26 (m0) / +0.34 (m1), so the candidate rule should use the 581-stream
rem per-window null max. To run the null sweep at campaign size (~4.2 h at 23k/s), change:
rem   set NULLKSB=work\h5rs\data\null581.ksb
set NULLKSB=work\h5rs\data\null8.ksb
set JOBLOG=work\tmp\h5rs_blocktest\bat_job.log

echo == h5rs flat-library campaign (blocks) start %date% %time% == >> %JOBLOG%
if not exist "%BIN%" goto :nobin

call :block 0 20 1
if errorlevel 1 goto :stop
call :block 20 40 2
if errorlevel 1 goto :stop
call :block 40 60 3
if errorlevel 1 goto :stop
call :block 60 80 4
if errorlevel 1 goto :stop
call :block 80 100 5
if errorlevel 1 goto :stop
call :nullsweep
if errorlevel 1 goto :stop

echo == campaign finished %date% %time% - merge with work\h5rs\merge_blocks.py == >> %JOBLOG%
exit /b 0

:nobin
echo ERROR: %BIN% not found - build it first: cargo build --release in work\h5rs >> %JOBLOG%
exit /b 1

:stop
echo campaign stopped - a block or the null sweep failed, see the log above >> %JOBLOG%
exit /b 1

:nullsweep
if not exist work\tmp\h5rs_blocktest\bat_null.done goto :nulrun
echo null sweep already done, skipping >> %JOBLOG%
exit /b 0
:nulrun
echo == null sweep start %date% %time% == > work\tmp\h5rs_blocktest\bat_null.log
%BIN% sweep %WIN% file:%NULLKSB% 0 100 2 20 2 8 work\tmp\h5rs_blocktest\bat_null.tsv --hits 1.5 --chunk 10 --progress 1 --best >> work\tmp\h5rs_blocktest\bat_null.log 2>&1
echo null sweep exit code %ERRORLEVEL% at %date% %time% >> work\tmp\h5rs_blocktest\bat_null.log
if errorlevel 1 exit /b 1
echo done %date% %time% > work\tmp\h5rs_blocktest\bat_null.done
exit /b 0

:block
rem %1 = off0, %2 = off1, %3 = block number
if not exist work\tmp\h5rs_blocktest\bat_block%3.done goto :blkrun
echo block %3 offs %1..%2 already done, skipping >> %JOBLOG%
exit /b 0
:blkrun
echo == block %3 offs %1..%2 start %date% %time% == > work\tmp\h5rs_blocktest\bat_block%3.log
%BIN% sweep %WIN% file:%LIB% %1 %2 2 20 2 8 work\tmp\h5rs_blocktest\bat_block%3.tsv --hits 1.5 --chunk 10 --progress 1 --best >> work\tmp\h5rs_blocktest\bat_block%3.log 2>&1
echo block %3 exit code %ERRORLEVEL% at %date% %time% >> work\tmp\h5rs_blocktest\bat_block%3.log
if errorlevel 1 goto :blkfail
echo done %date% %time% > work\tmp\h5rs_blocktest\bat_block%3.done
exit /b 0
:blkfail
echo block %3 FAILED - partial TSV kept for inspection, fix and relaunch, this block re-runs >> %JOBLOG%
exit /b 1
