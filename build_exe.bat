@echo off
setlocal

cd /d %~dp0
set "LOG_FILE=%~dp0build_exe.log"
echo ===== SitReminder build start %date% %time% ===== > "%LOG_FILE%"

set "PY_CMD="
where python >nul 2>nul
if %errorlevel%==0 set "PY_CMD=python"

if not defined PY_CMD (
  where py >nul 2>nul
  if %errorlevel%==0 set "PY_CMD=py -3"
)

if not defined PY_CMD (
  echo [ERROR] Python not found in PATH.
  echo Install Python 3.10+ and enable "Add python.exe to PATH", then retry.
  echo [ERROR] Python not found in PATH.>> "%LOG_FILE%"
  pause
  exit /b 1
)

echo Using: %PY_CMD%
echo Using: %PY_CMD%>> "%LOG_FILE%"

set "PYI_MODE="
set "OUT_HINT=dist\SitReminder\SitReminder.exe"
if defined ONEFILE (
  set "PYI_MODE=--onefile"
  set "OUT_HINT=dist\SitReminder.exe"
)

call %PY_CMD% -m pip install --upgrade pip >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

call %PY_CMD% -m pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

call %PY_CMD% -m pip install pyinstaller >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

call %PY_CMD% -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --windowed ^
  %PYI_MODE% ^
  --icon resources\icon.ico ^
  --add-data "resources;resources" ^
  --name SitReminder ^
  main.py >> "%LOG_FILE%" 2>&1
if errorlevel 1 goto :fail

if defined ONEFILE (
  if not exist dist\SitReminder.exe goto :fail
) else (
  if not exist dist\SitReminder\SitReminder.exe goto :fail
)

echo.
echo Build done: %OUT_HINT%
echo Build done: %OUT_HINT%>> "%LOG_FILE%"
echo Log file: %LOG_FILE%
if not defined NO_PAUSE pause
exit /b 0

:fail
echo.
echo Build failed. Please copy the error lines above and send them to me.
echo Build failed. See log: %LOG_FILE%
echo ===== Build failed %date% %time% =====>> "%LOG_FILE%"
if not defined NO_PAUSE pause
exit /b 1
