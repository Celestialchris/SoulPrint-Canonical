#!/usr/bin/env bash
# SoulPrint macOS Installer
# Downloads the latest SoulPrint release from GitHub and installs it
# to ~/Applications/. Preserves existing user data.
set -euo pipefail

REPO="Celestialchris/SoulPrint-Canonical"
API_URL="https://api.github.com/repos/${REPO}/releases/latest"
INSTALL_DIR="$HOME/Applications"
TEMP_DIR=$(mktemp -d)

echo "=== SoulPrint macOS Installer ==="
echo

# --- Check for curl ---
if ! command -v curl &>/dev/null; then
    echo "ERROR: curl not found. Please install curl."
    exit 1
fi

# --- Fetch release metadata ---
echo "Fetching latest release info..."
RELEASE_JSON=$(curl -sL "$API_URL")
if [ -z "$RELEASE_JSON" ]; then
    echo "ERROR: Failed to fetch release info from GitHub."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# --- Find macOS artifact URL ---
DOWNLOAD_URL=$(echo "$RELEASE_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for asset in data.get('assets', []):
    if 'macos' in asset['name'].lower():
        print(asset['browser_download_url'])
        break
" 2>/dev/null || true)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "ERROR: No macOS artifact found in the latest release."
    echo "Check https://github.com/${REPO}/releases manually."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# --- Download ---
echo "Downloading SoulPrint for macOS..."
curl -sL "$DOWNLOAD_URL" -o "$TEMP_DIR/SoulPrint-macos.zip"

# --- Install ---
echo "Installing to ${INSTALL_DIR}/..."
mkdir -p "$INSTALL_DIR"

# Preserve existing user data
if [ -d "$INSTALL_DIR/SoulPrint.app" ]; then
    echo "Removing previous SoulPrint.app (user data is stored separately)..."
    rm -rf "$INSTALL_DIR/SoulPrint.app"
fi

unzip -q "$TEMP_DIR/SoulPrint-macos.zip" -d "$INSTALL_DIR"

# --- Cleanup ---
rm -rf "$TEMP_DIR"

echo
echo "============================================"
echo "  SoulPrint installed to ${INSTALL_DIR}/SoulPrint.app"
echo
echo "  To run: open ${INSTALL_DIR}/SoulPrint.app"
echo "============================================"
echo
echo "NOTE: If macOS blocks SoulPrint.app, go to"
echo "  System Settings -> Privacy & Security"
echo "  and click \"Open Anyway\"."
