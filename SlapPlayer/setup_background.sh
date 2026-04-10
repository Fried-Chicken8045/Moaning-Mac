#!/bin/bash
# ============================================================
# SlapPlayer - Background Service Setup
# ============================================================
# Installs two background services:
#   1. Launch Daemon (root)  - reads accelerometer, plays sounds,
#                              writes trigger files for images
#   2. Launch Agent  (user)  - watches trigger files, shows image
#                              popups (needs GUI session access)
#
# Usage:  sudo ./setup_background.sh
# Remove: sudo ./setup_background.sh --uninstall
# ============================================================

set -e

SOURCE_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTALL_DIR="/usr/local/SlapPlayer"
DAEMON_PLIST="/Library/LaunchDaemons/com.slapplayer.plist"
LOG_DIR="$INSTALL_DIR/logs"

# Check sudo
if [ "$EUID" -ne 0 ]; then
    echo "[ERROR] Run with sudo:  sudo ./setup_background.sh"
    exit 1
fi

# Find the real user (not root)
REAL_USER="${SUDO_USER:-$(stat -f '%Su' /dev/console)}"
REAL_HOME=$(eval echo "~$REAL_USER")
AGENT_PLIST="$REAL_HOME/Library/LaunchAgents/com.slapplayer.agent.plist"

# ---- Uninstall --------------------------------------------------------
if [ "$1" = "--uninstall" ]; then
    echo "[..] Stopping services..."
    launchctl unload "$DAEMON_PLIST" 2>/dev/null || true
    sudo -u "$REAL_USER" launchctl unload "$AGENT_PLIST" 2>/dev/null || true
    rm -f "$DAEMON_PLIST" "$AGENT_PLIST"
    rm -rf "$INSTALL_DIR"
    rm -rf /tmp/slapplayer
    echo "[OK] SlapPlayer fully removed."
    exit 0
fi

# ---- Stop existing services -------------------------------------------
launchctl unload "$DAEMON_PLIST" 2>/dev/null || true
sudo -u "$REAL_USER" launchctl unload "$AGENT_PLIST" 2>/dev/null || true

# ---- Install files to /usr/local/SlapPlayer ---------------------------
echo "[..] Installing to $INSTALL_DIR ..."
rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

cp "$SOURCE_DIR/slap_player.py"  "$INSTALL_DIR/"
cp "$SOURCE_DIR/slap_agent.py"   "$INSTALL_DIR/"
cp "$SOURCE_DIR/image_popup.py"  "$INSTALL_DIR/"
cp -R "$SOURCE_DIR/sounds"       "$INSTALL_DIR/"
cp -R "$SOURCE_DIR/images"       "$INSTALL_DIR/"
[ -f "$SOURCE_DIR/icon.png" ] && cp "$SOURCE_DIR/icon.png" "$INSTALL_DIR/"
mkdir -p "$LOG_DIR"
chmod -R 755 "$INSTALL_DIR"
echo "[OK] Files copied"

# ---- Python environment -----------------------------------------------
echo "[..] Setting up Python environment..."
python3 -m venv "$INSTALL_DIR/.venv"
"$INSTALL_DIR/.venv/bin/pip" install --upgrade pip   > /dev/null 2>&1
"$INSTALL_DIR/.venv/bin/pip" install macimu rumps Pillow > /dev/null 2>&1
echo "[OK] Dependencies installed"

VENV_PYTHON="$INSTALL_DIR/.venv/bin/python3"

# ---- Launch Daemon (root — accelerometer + sound) ---------------------
cat > "$DAEMON_PLIST" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.slapplayer</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$INSTALL_DIR/slap_player.py</string>
        <string>--menubar</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key>
    <string>$LOG_DIR/daemon.log</string>
    <key>StandardErrorPath</key>
    <string>$LOG_DIR/daemon_error.log</string>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
</dict>
</plist>
PLIST
chmod 644 "$DAEMON_PLIST"

# ---- Launch Agent (user — image popups) -------------------------------
mkdir -p "$REAL_HOME/Library/LaunchAgents"
cat > "$AGENT_PLIST" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.slapplayer.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>$VENV_PYTHON</string>
        <string>$INSTALL_DIR/slap_agent.py</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key>
    <string>$REAL_HOME/Library/Logs/slapplayer_agent.log</string>
    <key>StandardErrorPath</key>
    <string>$REAL_HOME/Library/Logs/slapplayer_agent_error.log</string>
    <key>WorkingDirectory</key>
    <string>$INSTALL_DIR</string>
</dict>
</plist>
PLIST
chown "$REAL_USER" "$AGENT_PLIST"
chmod 644 "$AGENT_PLIST"

# ---- Start services ---------------------------------------------------
launchctl load "$DAEMON_PLIST"
sudo -u "$REAL_USER" launchctl load "$AGENT_PLIST"

echo ""
echo "  ============================================"
echo "  SlapPlayer Background Services Installed!"
echo "  ============================================"
echo ""
echo "  Daemon (accelerometer + sound): running as root"
echo "  Agent  (image popups):          running as $REAL_USER"
echo ""
echo "  Add sounds: $INSTALL_DIR/sounds/"
echo "  Add images: $INSTALL_DIR/images/"
echo ""
echo "  Logs:"
echo "    tail -f $LOG_DIR/daemon.log"
echo "    tail -f $LOG_DIR/agent.log"
echo ""
echo "  Uninstall: sudo $SOURCE_DIR/setup_background.sh --uninstall"
echo ""
