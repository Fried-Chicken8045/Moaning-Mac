#!/usr/bin/env python3
"""
SlapPlayer - Slap your Mac, hear a sound and see a picture!

Detects physical slaps on your MacBook via the built-in accelerometer
(Apple Silicon M1-M4), plays a random sound, and pops up a random image.

Usage:
    sudo python3 slap_player.py              # Terminal mode
    sudo python3 slap_player.py --menubar    # Menu bar mode (requires rumps)
    sudo python3 slap_player.py --threshold 1.1  # Custom sensitivity

Requirements:
    - Apple Silicon Mac (M1/M2/M3/M4)
    - Python 3.9+
    - macimu package (pip install macimu)
    - rumps package for menu bar mode (pip install rumps)
    - Pillow for image scaling (pip install Pillow) - optional but recommended
    - Must run with sudo for accelerometer access
"""

import os
import sys
import random
import subprocess
import time
import math
import threading
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SOUNDS_DIR   = Path(__file__).parent / "sounds"
IMAGES_DIR   = Path(__file__).parent / "images"
TRIGGER_DIR  = Path("/tmp/slapplayer")  # Agent watches this for image triggers
DISABLED_FLAG = TRIGGER_DIR / "disabled"  # Agent writes this to pause everything

DEFAULT_THRESHOLD = 1.1   # g-force magnitude to count as a "slap" (rest is ~1.0g)
DEFAULT_COOLDOWN  = 6.0   # seconds between triggers (prevents rapid-fire)
IMAGE_DURATION    = 6     # seconds the image popup stays on screen

SUPPORTED_SOUNDS  = {".mp3", ".wav", ".aiff", ".m4a", ".aac", ".ogg", ".flac"}
SUPPORTED_IMAGES  = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_console_user():
    """Return the username of whoever is logged into the GUI session."""
    try:
        result = subprocess.run(
            ["stat", "-f", "%Su", "/dev/console"],
            capture_output=True, text=True
        )
        user = result.stdout.strip()
        if user and user != "root":
            return user
    except Exception:
        pass
    return os.environ.get("SUDO_USER") or os.environ.get("USER") or "nobody"


# ---------------------------------------------------------------------------
# Core slap detection + sound + image playback
# ---------------------------------------------------------------------------

class SlapPlayer:
    """Monitors accelerometer for slaps, plays sounds, and shows images."""

    def __init__(self, sounds_dir=SOUNDS_DIR, images_dir=IMAGES_DIR,
                 threshold=DEFAULT_THRESHOLD, cooldown=DEFAULT_COOLDOWN):
        self.sounds_dir = Path(sounds_dir)
        self.images_dir = Path(images_dir)
        self.threshold  = threshold
        self.cooldown   = cooldown
        self.last_trigger = 0.0
        self.enabled    = True
        self.sound_files = []
        self.image_files = []
        self.slap_count  = 0
        self._on_slap_callbacks = []
        self.reload_sounds()
        self.reload_images()

    # -- File management ----------------------------------------------------

    def reload_sounds(self):
        self.sound_files = []
        if self.sounds_dir.exists():
            self.sound_files = sorted(
                f for f in self.sounds_dir.iterdir()
                if f.is_file() and f.suffix.lower() in SUPPORTED_SOUNDS
            )
        print(f"[SlapPlayer] Loaded {len(self.sound_files)} sound(s)")
        return len(self.sound_files)

    def reload_images(self):
        self.image_files = []
        if self.images_dir.exists():
            self.image_files = sorted(
                f for f in self.images_dir.iterdir()
                if f.is_file() and f.suffix.lower() in SUPPORTED_IMAGES
            )
        print(f"[SlapPlayer] Loaded {len(self.image_files)} image(s)")
        return len(self.image_files)

    # -- Playback -----------------------------------------------------------

    def play_random_sound(self):
        if not self.sound_files:
            return
        sound = random.choice(self.sound_files)
        subprocess.Popen(
            ["afplay", str(sound)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        print(f"[SlapPlayer] Sound: {sound.name}")

    def show_random_image(self):
        if not self.image_files:
            return
        image = random.choice(self.image_files)
        print(f"[SlapPlayer] Image: {image.name}")

        # Write a trigger file for the Launch Agent (slap_agent.py) to pick up.
        # The agent runs in the user's GUI session so it can show windows —
        # the daemon (this process) cannot access the display directly.
        try:
            import pwd
            console_user = get_console_user()
            pw = pwd.getpwnam(console_user)
            uid, gid = pw.pw_uid, pw.pw_gid

            # Create dir owned by the console user so they can delete files in it
            TRIGGER_DIR.mkdir(parents=True, exist_ok=True)
            os.chown(str(TRIGGER_DIR), uid, gid)
            os.chmod(str(TRIGGER_DIR), 0o755)

            trigger = TRIGGER_DIR / f"{time.time()}.trigger"
            trigger.write_text(str(image))
            os.chown(str(trigger), uid, gid)  # User owns the file → can delete it
            os.chmod(str(trigger), 0o644)
        except Exception as e:
            print(f"[SlapPlayer] Could not write trigger: {e}")

    # -- Slap detection -----------------------------------------------------

    def on_slap(self, callback):
        self._on_slap_callbacks.append(callback)

    def _handle_accel(self, sample):
        if not self.enabled:
            return
        if DISABLED_FLAG.exists():
            return
        x, y, z = sample
        magnitude = math.sqrt(x * x + y * y + z * z)
        now = time.time()
        if magnitude > self.threshold and (now - self.last_trigger) > self.cooldown:
            self.last_trigger = now
            self.slap_count += 1
            print(f"[SlapPlayer] SLAP #{self.slap_count}! ({magnitude:.2f}g)")
            # Play sound and show image in parallel
            threading.Thread(target=self.play_random_sound, daemon=True).start()
            threading.Thread(target=self.show_random_image,  daemon=True).start()
            for cb in self._on_slap_callbacks:
                try:
                    cb(magnitude)
                except Exception:
                    pass

    # -- Main loop ----------------------------------------------------------

    def start(self):
        """Start monitoring the accelerometer. Blocks until interrupted."""
        try:
            from macimu import IMU
        except ImportError:
            print("\n[ERROR] 'macimu' package not found.")
            print("Install it with:  pip install macimu\n")
            sys.exit(1)

        try:
            imu = IMU()
            imu.on_accel(self._handle_accel)
            imu.start()
        except Exception as e:
            print(f"\n[ERROR] Could not access accelerometer: {e}")
            print("Make sure you are running with sudo on Apple Silicon.\n")
            sys.exit(1)

        print(f"[SlapPlayer] Accelerometer active! "
              f"(threshold={self.threshold}g, cooldown={self.cooldown}s)")
        print(f"[SlapPlayer] Console user: {self.console_user}")
        print("[SlapPlayer] Slap your Mac! Ctrl+C to quit.\n")

        # IOKit HID callbacks need a CFRunLoop to fire in background threads
        try:
            from Foundation import NSRunLoop, NSDate
            while True:
                NSRunLoop.currentRunLoop().runUntilDate_(
                    NSDate.dateWithTimeIntervalSinceNow_(1.0)
                )
        except ImportError:
            try:
                import ctypes
                CF = ctypes.cdll.LoadLibrary(
                    "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation"
                )
                mode = ctypes.c_void_p.in_dll(CF, "kCFRunLoopDefaultMode")
                while True:
                    CF.CFRunLoopRunInMode(mode, 1.0, False)
            except Exception:
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n[SlapPlayer] Goodbye!")


# ---------------------------------------------------------------------------
# Menu bar app (optional, requires 'rumps')
# ---------------------------------------------------------------------------

def run_menubar(player):
    try:
        import rumps
    except ImportError:
        print("[WARN] 'rumps' not installed. Falling back to terminal mode.")
        player.start()
        return

    class SlapMenuApp(rumps.App):
        def __init__(self):
            super().__init__("SlapPlayer", title="\U0001F44B")
            self.player = player

            self.sound_count_item  = rumps.MenuItem(f"Sounds: {len(player.sound_files)}")
            self.image_count_item  = rumps.MenuItem(f"Images: {len(player.image_files)}")
            self.slap_count_item   = rumps.MenuItem("Slaps: 0")
            self.enabled_item      = rumps.MenuItem("Enabled", callback=self.toggle_enabled)
            self.enabled_item.state = True

            sens_menu = rumps.MenuItem("Sensitivity")
            for label, val in [("Very Light (1.2g)", 1.2), ("Light (1.5g)", 1.5),
                                ("Normal (2.0g)", 2.0),  ("Hard (3.0g)", 3.0)]:
                item = rumps.MenuItem(label, callback=self._make_sens_cb(val))
                item.state = (val == player.threshold)
                sens_menu[label] = item
            self.sens_menu = sens_menu

            self.menu = [
                self.enabled_item,
                None,
                self.sound_count_item,
                self.image_count_item,
                self.slap_count_item,
                None,
                rumps.MenuItem("Reload Sounds", callback=self.reload_sounds),
                rumps.MenuItem("Reload Images", callback=self.reload_images),
                self.sens_menu,
                None,
                rumps.MenuItem("Open Sounds Folder", callback=self.open_sounds),
                rumps.MenuItem("Open Images Folder", callback=self.open_images),
            ]

            player.on_slap(self._on_slap)

        def _make_sens_cb(self, val):
            def cb(sender):
                self.player.threshold = val
                for item in self.sens_menu.values():
                    if isinstance(item, rumps.MenuItem):
                        item.state = False
                sender.state = True
            return cb

        def toggle_enabled(self, sender):
            sender.state = not sender.state
            self.player.enabled = sender.state

        def reload_sounds(self, _):
            count = self.player.reload_sounds()
            self.sound_count_item.title = f"Sounds: {count}"
            rumps.notification("SlapPlayer", "", f"Loaded {count} sound(s)")

        def reload_images(self, _):
            count = self.player.reload_images()
            self.image_count_item.title = f"Images: {count}"
            rumps.notification("SlapPlayer", "", f"Loaded {count} image(s)")

        def open_sounds(self, _):
            subprocess.Popen(["open", str(self.player.sounds_dir)])

        def open_images(self, _):
            subprocess.Popen(["open", str(self.player.images_dir)])

        def _on_slap(self, magnitude):
            self.slap_count_item.title = f"Slaps: {self.player.slap_count}"

    threading.Thread(target=player.start, daemon=True).start()
    SlapMenuApp().run()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SlapPlayer - Slap your Mac!")
    parser.add_argument("--menubar",   action="store_true")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    parser.add_argument("--cooldown",  type=float, default=DEFAULT_COOLDOWN)
    parser.add_argument("--sounds",    type=str,   default=str(SOUNDS_DIR))
    parser.add_argument("--images",    type=str,   default=str(IMAGES_DIR))
    args = parser.parse_args()

    if sys.platform != "darwin":
        print("[ERROR] SlapPlayer only works on macOS with Apple Silicon.")
        sys.exit(1)

    if os.geteuid() != 0:
        print("[SlapPlayer] Restarting with sudo for accelerometer access...\n")
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)

    player = SlapPlayer(
        sounds_dir=args.sounds,
        images_dir=args.images,
        threshold=args.threshold,
        cooldown=args.cooldown,
    )

    if args.menubar:
        run_menubar(player)
    else:
        player.start()


if __name__ == "__main__":
    main()
