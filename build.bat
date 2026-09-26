@echo off
setlocal
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
set "UPX_DIR=%CD%\.build-tools\upx-5.2.1\upx-5.2.1-win64"

if not exist "%PY%" (
    py -3 -m venv .venv 2>nul || python -m venv .venv
)
if errorlevel 1 goto :fail

"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto :fail

"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

powershell -NoProfile -ExecutionPolicy Bypass -File "tools\ensure_upx.ps1"
if errorlevel 1 goto :fail
if not exist "%UPX_DIR%\upx.exe" goto :fail

"%PY%" tools\create_icon.py
if errorlevel 1 goto :fail
tasklist /FI "IMAGENAME eq ButtonWatcher.exe" | find /I "ButtonWatcher.exe" >nul
if not errorlevel 1 (
    echo ERROR: ButtonWatcher.exe is currently running. Close it and run build.bat again.
    exit /b 1
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

"%PY%" -m PyInstaller --noconfirm --clean --upx-dir "%UPX_DIR%" button_watcher.spec
if errorlevel 1 goto :fail

if not exist "dist\ButtonWatcher.exe" (
    echo ERROR: dist\ButtonWatcher.exe was not created.
    exit /b 1
)

echo.
echo Build complete: %CD%\dist\ButtonWatcher.exe
exit /b 0

:fail
echo.
echo Build failed.
exit /b 1
