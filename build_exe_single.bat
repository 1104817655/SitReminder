@echo off
setlocal

cd /d %~dp0
set "NO_PAUSE=1"
set "ONEFILE=1"

call build_exe.bat
if errorlevel 1 (
  echo.
  echo Single-file EXE build failed. Check build_exe.log.
  pause
  exit /b 1
)

echo.
echo Single-file build done.
echo EXE:
echo   dist\SitReminder.exe
pause
