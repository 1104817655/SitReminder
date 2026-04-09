@echo off
setlocal

cd /d %~dp0
set "NO_PAUSE=1"

echo [1/2] Building EXE...
call build_exe.bat
if errorlevel 1 goto :fail_exe

echo.
echo [2/2] Building Installer...
call build_installer.bat
if errorlevel 1 goto :fail_installer

echo.
echo All done.
echo EXE: dist\SitReminder\SitReminder.exe
echo Installer: dist\installer\SitReminder-Setup.exe
pause
exit /b 0

:fail_exe
echo.
echo EXE build failed. Check build_exe.log for details.
pause
exit /b 1

:fail_installer
echo.
echo Installer build failed.
echo If the error says iscc not found, install Inno Setup 6 first.
pause
exit /b 1
