@echo off
setlocal

cd /d %~dp0
set "NO_PAUSE=1"

call build_exe.bat
if errorlevel 1 (
  echo.
  echo Portable EXE build failed. Check build_exe.log.
  pause
  exit /b 1
)

echo.
echo Portable build done.
echo Folder to distribute:
echo   dist\SitReminder\
echo Main exe:
echo   dist\SitReminder\SitReminder.exe
pause
