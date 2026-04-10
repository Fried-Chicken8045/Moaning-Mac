#!/bin/bash
# ============================================================
# SlapPlayer - Installation Script
# ============================================================
# This script sets up a Python virtual environment and installs
# all dependencies needed for SlapPlayer.
#
# Usage:  chmod +x install.sh && ./install.sh
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo ""
echo "  ============================================"
echo "  SlapPlayer Installer"
echo "  ============================================"
echo ""

# Check macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo "[ERROR] SlapPlayer only works on macOS with Apple Silicon."
    exit 1
fi

# Check for Apple Silicon
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    echo "[WARNING] You appear to be on an Intel Mac ($ARCH)."
    echo "          SlapPlayer's accelerometer detection requires Apple Silicon (M1+)."
    echo "          Installation will continue, but the app may not work."
    echo ""
fi

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found. Install it from https://python.org or via Homebrew:"
    echo "        brew install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[OK] Found Python $PYTHON_VERSION"

# Create virtual environment
echo "[..] Creating virtual environment at $VENV_DIR ..."
python3 -m venv "$VENV_DIR"
echo "[OK] Virtual environment created"

# Activate and install packages
echo "[..] Installing dependencies..."
source "$VENV_DIR/bin/activate"

pip install --upgrade pip > /dev/null 2>&1
pip install macimu rumps Pillow > /dev/null 2>&1

echo "[OK] Installed: macimu (accelerometer), rumps (menu bar), Pillow (images)"

# Create sounds directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/sounds"

# Check for sound files
SOUND_COUNT=$(find "$SCRIPT_DIR/sounds" -type f \( -name "*.mp3" -o -name "*.wav" -o -name "*.aiff" -o -name "*.m4a" -o -name "*.aac" -o -name "*.ogg" -o -name "*.flac" \) 2>/dev/null | wc -l | tr -d ' ')

echo ""
echo "  ============================================"
echo "  Installation Complete!"
echo "  ============================================"
echo ""
echo "  Sound files found: $SOUND_COUNT"
if [ "$SOUND_COUNT" -eq "0" ]; then
    echo ""
    echo "  >> Add your sound files (.mp3, .wav, etc.) to:"
    echo "     $SCRIPT_DIR/sounds/"
    echo ""
fi
echo "  To run (terminal mode):"
echo "    sudo $VENV_DIR/bin/python3 $SCRIPT_DIR/slap_player.py"
echo ""
echo "  To run (menu bar mode):"
echo "    sudo $VENV_DIR/bin/python3 $SCRIPT_DIR/slap_player.py --menubar"
echo ""
echo "  Or use the launcher:"
echo "    ./launch.sh"
echo ""
