@echo off
REM SoulPrint Windows Installer
REM Downloads the latest SoulPrint release from GitHub and installs it.
REM Prefers SoulPrint-Setup.exe (installer); falls back to zip extraction.
REM Preserves existing user data in instance\.
setlocal enabledelayedexpansion

set "REPO=Celestialchris/SoulPrint-Canonical"
set "API_URL=https://api.github.com/repos/%REPO%/releases/latest"
set "INSTALL_DIR=%LOCALAPPDATA%\SoulPrint"
set "TEMP_DIR=%TEMP%\soulprint-install"

echo === SoulPrint Installer ===
echo.

REM --- Check for curl ---
where curl >nul 2>nul
if errorlevel 1 (
    echo ERROR: curl not found. Please install curl or use Windows 10+.
    exit /b 1
)

REM --- Fetch release metadata ---
echo Fetching latest release info...
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
curl -sL "%API_URL%" -o "%TEMP_DIR%\release.json"
if errorlevel 1 (
    echo ERROR: Failed to fetch release info from GitHub.
    exit /b 1
)

REM --- Try to find SoulPrint-Setup.exe first, then zip ---
set "DOWNLOAD_URL="
set "ARTIFACT_TYPE="

for /f "delims=" %%u in ('powershell -NoProfile -Command "$r = Get-Content '%TEMP_DIR%\release.json' | ConvertFrom-Json; $a = $r.assets | Where-Object { $_.name -like '*Setup*' }; if ($a) { $a[0].browser_download_url } else { ($r.assets | Where-Object { $_.name -like '*windows*' })[0].browser_download_url }"') do set "DOWNLOAD_URL=%%u"

for /f "delims=" %%t in ('powershell -NoProfile -Command "$r = Get-Content '%TEMP_DIR%\release.json' | ConvertFrom-Json; $a = $r.assets | Where-Object { $_.name -like '*Setup*' }; if ($a) { echo 'installer' } else { echo 'zip' }"') do set "ARTIFACT_TYPE=%%t"

if "%DOWNLOAD_URL%"=="" (
    echo ERROR: No Windows artifact found in the latest release.
    echo Check https://github.com/%REPO%/releases manually.
    exit /b 1
)

REM --- Download ---
echo Downloading SoulPrint (%ARTIFACT_TYPE%)...
if "%ARTIFACT_TYPE%"=="installer" (
    curl -sL "%DOWNLOAD_URL%" -o "%TEMP_DIR%\SoulPrint-Setup.exe"
) else (
    curl -sL "%DOWNLOAD_URL%" -o "%TEMP_DIR%\SoulPrint-windows.zip"
)
if errorlevel 1 (
    echo ERROR: Download failed.
    exit /b 1
)

REM --- Install ---
if "%ARTIFACT_TYPE%"=="installer" (
    echo Running installer...
    start "" "%TEMP_DIR%\SoulPrint-Setup.exe"
    echo Installer launched. Follow the prompts to complete installation.
) else (
    echo Installing to %INSTALL_DIR%...

    REM Preserve existing user data
    if exist "%INSTALL_DIR%\instance" (
        echo Preserving existing user data...
        move "%INSTALL_DIR%\instance" "%TEMP_DIR%\instance_backup" >nul
    )

    if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%TEMP_DIR%\SoulPrint-windows.zip' -DestinationPath '%INSTALL_DIR%' -Force"

    REM Restore user data
    if exist "%TEMP_DIR%\instance_backup" (
        move "%TEMP_DIR%\instance_backup" "%INSTALL_DIR%\instance" >nul
        echo User data restored.
    )

    echo.
    echo ============================================
    echo   SoulPrint installed to %INSTALL_DIR%
    echo   Run: %INSTALL_DIR%\SoulPrint.exe
    echo ============================================
)

REM --- Cleanup ---
rmdir /s /q "%TEMP_DIR%" >nul 2>nul
endlocal
