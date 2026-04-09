@echo off
setlocal

cd /d %~dp0

if not exist dist\SitReminder\SitReminder.exe (
  echo SitReminder.exe not found.
  echo Please run build_exe.bat first.
  if not defined NO_PAUSE pause
  exit /b 1
)

where iscc >nul 2>nul
if errorlevel 1 (
  echo Inno Setup (iscc) not found in PATH.
  echo Install Inno Setup 6 and add iscc to PATH, then retry.
  if not defined NO_PAUSE pause
  exit /b 1
)

iscc installer\SitReminder.iss
if errorlevel 1 (
  echo Installer build failed.
  if not defined NO_PAUSE pause
  exit /b 1
)

echo.
echo Installer done: dist\installer\SitReminder-Setup.exe
if not defined NO_PAUSE pause
