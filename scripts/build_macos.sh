#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== SoulPrint macOS Build ==="
echo

# --- Version from pyproject.toml ---
VERSION=$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
echo "Version: $VERSION"
echo

# --- Virtual environment ---
if [ ! -d .venv ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi
source .venv/bin/activate

echo "Installing dependencies..."
python3 -m pip install --upgrade pip
pip install -e ".[build,full,dev,intelligence]"

echo
echo "Running tests..."
python3 -m pytest tests/ -v
echo

echo "Building with PyInstaller..."
pyinstaller --noconfirm --clean scripts/SoulPrint.spec

echo
echo "=== Packaging ==="

# --- Code signing (optional) ---
if [ -n "${CODESIGN_IDENTITY:-}" ]; then
    echo "Signing SoulPrint.app with identity: $CODESIGN_IDENTITY"
    codesign --force --deep --sign "$CODESIGN_IDENTITY" dist/SoulPrint.app
    echo "Signed."
else
    echo "No CODESIGN_IDENTITY set — producing unsigned build."
    echo "To sign, run: CODESIGN_IDENTITY='Developer ID Application: ...' $0"
fi

# --- Zip ---
ARTIFACT="dist/SoulPrint-${VERSION}-macos.zip"
rm -f "$ARTIFACT"
cd dist
zip -r -y "../${ARTIFACT}" SoulPrint.app
cd ..

echo
echo "============================================"
echo "  Build complete!"
echo
echo "  App:     dist/SoulPrint.app"
echo "  Zip:     $ARTIFACT"
echo "  Version: $VERSION"
echo "============================================"
