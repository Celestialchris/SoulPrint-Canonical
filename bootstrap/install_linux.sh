#!/usr/bin/env bash
# SoulPrint Linux Installer
# Downloads the latest SoulPrint release from GitHub, extracts it
# to ~/.local/share/SoulPrint/, and creates a .desktop launcher.
# Preserves existing user data in instance/.
set -euo pipefail

REPO="Celestialchris/SoulPrint-Canonical"
API_URL="https://api.github.com/repos/${REPO}/releases/latest"
INSTALL_DIR="$HOME/.local/share/SoulPrint"
DESKTOP_DIR="$HOME/.local/share/applications"
TEMP_DIR=$(mktemp -d)

echo "=== SoulPrint Linux Installer ==="
echo

# --- Check for curl ---
if ! command -v curl &>/dev/null; then
    echo "ERROR: curl not found. Install it with your package manager:"
    echo "  sudo apt install curl    # Debian/Ubuntu"
    echo "  sudo dnf install curl    # Fedora"
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

# --- Find Linux artifact URL ---
DOWNLOAD_URL=$(echo "$RELEASE_JSON" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for asset in data.get('assets', []):
    if 'linux' in asset['name'].lower():
        print(asset['browser_download_url'])
        break
" 2>/dev/null || true)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "ERROR: No Linux artifact found in the latest release."
    echo "Check https://github.com/${REPO}/releases manually."
    rm -rf "$TEMP_DIR"
    exit 1
fi

# --- Download ---
echo "Downloading SoulPrint for Linux..."
curl -sL "$DOWNLOAD_URL" -o "$TEMP_DIR/SoulPrint-linux.tar.gz"

# --- Install ---
echo "Installing to ${INSTALL_DIR}/..."
mkdir -p "$INSTALL_DIR"

# Preserve existing user data
if [ -d "$INSTALL_DIR/instance" ]; then
    echo "Preserving existing user data..."
    mv "$INSTALL_DIR/instance" "$TEMP_DIR/instance_backup"
fi

# Extract (overwrites old binaries)
tar -xzf "$TEMP_DIR/SoulPrint-linux.tar.gz" -C "$INSTALL_DIR" --strip-components=1

# Restore user data
if [ -d "$TEMP_DIR/instance_backup" ]; then
    mv "$TEMP_DIR/instance_backup" "$INSTALL_DIR/instance"
    echo "User data restored."
fi

# --- Desktop launcher ---
mkdir -p "$DESKTOP_DIR"
cat > "$DESKTOP_DIR/soulprint.desktop" << DESKTOP
[Desktop Entry]
Type=Application
Name=SoulPrint
Comment=Your AI conversations, brought home
Exec=${INSTALL_DIR}/SoulPrint
Terminal=false
Categories=Utility;
DESKTOP

echo

# --- Cleanup ---
rm -rf "$TEMP_DIR"

echo "============================================"
echo "  SoulPrint installed to ${INSTALL_DIR}/"
echo "  Desktop launcher created."
echo
echo "  To run: ${INSTALL_DIR}/SoulPrint"
echo "  Or find \"SoulPrint\" in your application menu."
echo "============================================"
