@echo off
setlocal
cd /d "%~dp0"

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
    py -3 -m venv .venv 2>nul || python -m venv .venv
)
if errorlevel 1 goto :fail

"%PY%" -m pip install --upgrade pip
if errorlevel 1 goto :fail

"%PY%" -m pip install -r requirements.txt
if errorlevel 1 goto :fail

"%PY%" tools\create_icon.py
if errorlevel 1 goto :fail

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

"%PY%" -m PyInstaller --noconfirm --clean button_watcher.spec
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
