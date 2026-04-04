#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== SoulPrint Linux Build ==="
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
pip install -r requirements.txt
pip install -e ".[build,full,dev]"

echo
echo "Running tests..."
python3 -m pytest tests/ -v
echo

echo "Building with PyInstaller..."
pyinstaller --noconfirm --clean scripts/SoulPrint.spec

echo
echo "=== Packaging ==="
ARTIFACT="dist/SoulPrint-${VERSION}-linux.tar.gz"
rm -f "$ARTIFACT"
tar -czf "$ARTIFACT" -C dist SoulPrint

echo
echo "============================================"
echo "  Build complete!"
echo
echo "  Folder:  dist/SoulPrint/"
echo "  Exe:     dist/SoulPrint/SoulPrint"
echo "  Archive: $ARTIFACT"
echo "  Version: $VERSION"
echo "============================================"
