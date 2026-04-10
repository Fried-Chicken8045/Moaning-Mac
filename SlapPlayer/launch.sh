#!/bin/bash
# ============================================================
# SlapPlayer - Quick Launcher
# ============================================================
# Launches SlapPlayer in menu bar mode using the virtual env.
# Automatically requests sudo for accelerometer access.
#
# Usage:  chmod +x launch.sh && ./launch.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python3"

# Check venv exists
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] Virtual environment not found."
    echo "        Run ./install.sh first!"
    exit 1
fi

echo "[SlapPlayer] Starting in menu bar mode..."
echo "[SlapPlayer] You may be prompted for your password (sudo required for accelerometer)."
echo ""

sudo "$VENV_PYTHON" "$SCRIPT_DIR/slap_player.py" --menubar
