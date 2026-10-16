@echo off
rem Daily news digest launcher.
rem ASCII-only on purpose: cmd.exe reads .bat files in the OEM/GBK codepage,
rem so literal CJK here would corrupt. %~dp0 self-locates instead.
cd /d "%~dp0"
if not exist "%~dp0output" mkdir "%~dp0output"
echo [%date% %time%] ---- run start ---- >> "%~dp0output\run.log"
"C:\Python314\python.exe" "%~dp0fetch.py" >> "%~dp0output\run.log" 2>&1
echo [%date% %time%] ---- exit=%errorlevel% ---- >> "%~dp0output\run.log"
exit /b %errorlevel%
