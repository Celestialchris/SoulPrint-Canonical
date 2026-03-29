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
echo === Step 4: Inno Setup Installer ===
set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if exist "%ISCC_PATH%" (
    "%ISCC_PATH%" scripts\SoulPrint.iss
    if errorlevel 1 (
        echo.
        echo WARNING: Inno Setup compilation failed.
        echo The portable build is still at dist\SoulPrint\SoulPrint.exe
    ) else (
        echo Installer: dist\SoulPrint-Setup.exe
    )
) else (
    where ISCC >nul 2>nul
    if not errorlevel 1 (
        ISCC scripts\SoulPrint.iss
        echo Installer: dist\SoulPrint-Setup.exe
    ) else (
        echo Inno Setup not found. Install from https://jrsoftware.org/isdl.php
        echo Then add ISCC.exe to PATH, or compile scripts\SoulPrint.iss manually.
        echo The portable build is still at dist\SoulPrint\SoulPrint.exe
    )
)

echo.
echo ============================================
echo   Build complete!
echo.
echo   Folder:    dist\SoulPrint\
echo   Exe:       dist\SoulPrint\SoulPrint.exe
echo   Zip:       dist\SoulPrint-windows.zip
if exist dist\SoulPrint-Setup.exe echo   Installer: dist\SoulPrint-Setup.exe
echo ============================================
endlocal
