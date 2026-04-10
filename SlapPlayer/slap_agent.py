#!/usr/bin/env python3
"""
slap_agent.py - Runs as a Launch Agent (in your GUI session).

- Shows a 👋 menu bar icon with an on/off toggle
- Watches /tmp/slapplayer/*.trigger files written by the daemon
- Displays image popups when a trigger is detected
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path

TRIGGER_DIR   = Path("/tmp/slapplayer")
DISABLED_FLAG = TRIGGER_DIR / "disabled"
POPUP_SCRIPT  = Path(__file__).parent / "image_popup.py"
ICON_FILE     = Path(__file__).parent / "icon.png"
PYTHON        = sys.executable
POLL_INTERVAL = 0.1


def handle_trigger(trigger_file):
    try:
        image_path = trigger_file.read_text().strip()
        if not image_path or not Path(image_path).exists():
            print(f"[slap_agent] Image not found: {image_path}")
        else:
            print(f"[slap_agent] Showing: {image_path}")
            subprocess.Popen(
                [PYTHON, str(POPUP_SCRIPT), image_path, "--duration", "6"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
    except Exception as e:
        print(f"[slap_agent] Error reading trigger: {e}")
    finally:
        # Always try to delete — fail silently if permission denied
        try:
            trigger_file.unlink()
        except Exception:
            # Can't delete (sticky bit) — rename to .done so we don't reprocess
            try:
                trigger_file.rename(trigger_file.with_suffix(".done"))
            except Exception:
                pass


def watch_loop():
    TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
    # Start disabled — user must toggle on via menu bar
    DISABLED_FLAG.touch()
    print(f"[slap_agent] Watching {TRIGGER_DIR} (starting disabled)")
    processed = set()
    while True:
        try:
            for f in TRIGGER_DIR.glob("*.trigger"):
                if f.name not in processed:
                    processed.add(f.name)
                    threading.Thread(target=handle_trigger, args=(f,), daemon=True).start()
            # Keep processed set from growing forever
            if len(processed) > 500:
                processed.clear()
        except Exception as e:
            print(f"[slap_agent] Poll error: {e}")
        time.sleep(POLL_INTERVAL)


def main():
    try:
        import rumps
    except ImportError:
        print("[slap_agent] rumps not installed — running without menu bar")
        watch_loop()
        return

    # Start watcher in background thread
    threading.Thread(target=watch_loop, daemon=True).start()

    class SlapAgentApp(rumps.App):
        def __init__(self):
            icon = str(ICON_FILE) if ICON_FILE.exists() else None
            super().__init__(
                "SlapAgent",
                icon=icon,
                title=None if icon else "🤚",
                template=False,
            )
            self.enabled = False
            self.toggle_item = rumps.MenuItem("Turn On", callback=self.toggle)
            self.toggle_item.state = False
            self.menu = [
                self.toggle_item,
            ]

        def toggle(self, sender):
            self.enabled = not self.enabled
            TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
            has_icon = ICON_FILE.exists()
            if self.enabled:
                DISABLED_FLAG.unlink(missing_ok=True)
                if not has_icon:
                    self.title = "👋"
                sender.title = "Turn Off"
                print("[slap_agent] Enabled")
            else:
                DISABLED_FLAG.touch()
                if not has_icon:
                    self.title = "🤚"
                sender.title = "Turn On"
                print("[slap_agent] Disabled")

    SlapAgentApp().run()


if __name__ == "__main__":
    main()
