@echo off
rem ============================================================
rem  One-click stop for the daily news digest scheduled task.
rem  Double-click this file. It will ask for admin rights (UAC),
rem  remove the task, and verify it is gone.
rem  ASCII-only body on purpose (cmd reads .bat in the OEM/GBK
rem  codepage, so literal CJK here would corrupt).
rem ============================================================
setlocal
set TASK=DailyNewsDigest

net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrator rights...
    powershell -NoProfile -Command "Start-Process -FilePath 'schtasks.exe' -Verb RunAs -Wait -ArgumentList '/delete','/tn','%TASK%','/f'"
    goto :verify
)

schtasks /end /tn "%TASK%" >nul 2>&1
schtasks /delete /tn "%TASK%" /f

:verify
echo.
schtasks /query /tn "%TASK%" >nul 2>&1
if %errorlevel% neq 0 (
    echo [OK] Task "%TASK%" has been removed.
    echo      The daily digest will no longer run.
) else (
    echo [WARN] Task "%TASK%" still exists.
    echo        Right-click this file and choose "Run as administrator".
)
echo.
pause
