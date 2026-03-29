@echo off
setlocal enabledelayedexpansion
cd /d %~dp0\..

echo === SoulPrint Windows Build ===
echo.

if not exist .venv (
    echo Creating virtual environment...
    py -3.12 -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e ".[build,full,dev]"

echo.
echo Running tests...
python -m pytest
if errorlevel 1 (
    echo.
    echo ERROR: Tests failed. Build aborted.
    exit /b 1
)

echo.
echo Building with PyInstaller...
pyinstaller --noconfirm --clean scripts\SoulPrint.spec
if errorlevel 1 (
    echo.
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

echo.
echo Packaging zip...
if exist dist\SoulPrint-windows.zip del /f /q dist\SoulPrint-windows.zip
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path dist\SoulPrint\* -DestinationPath dist\SoulPrint-windows.zip -Force"

echo.
echo ============================================
echo   Build complete!
echo.
echo   Folder: dist\SoulPrint\
echo   Exe:    dist\SoulPrint\SoulPrint.exe
echo   Zip:    dist\SoulPrint-windows.zip
echo ============================================
endlocal
