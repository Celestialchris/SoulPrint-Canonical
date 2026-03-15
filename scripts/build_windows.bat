@echo off
setlocal enabledelayedexpansion
cd /d %~dp0\..

if not exist .venv (
    py -3.12 -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-minimal.txt -r requirements-build.txt
pip install -e .

python -m pytest
if errorlevel 1 (
    echo Tests failed. Build aborted.
    exit /b 1
)

pyinstaller --noconfirm --clean SoulPrint.spec
if errorlevel 1 (
    echo PyInstaller build failed.
    exit /b 1
)

if exist dist\SoulPrint-windows.zip del /f /q dist\SoulPrint-windows.zip
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path dist\SoulPrint\* -DestinationPath dist\SoulPrint-windows.zip -Force"

echo.
echo Build complete:
echo   dist\SoulPrint\
echo   dist\SoulPrint-windows.zip
endlocal
