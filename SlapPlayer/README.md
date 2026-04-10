# SlapPlayer

Slap your MacBook — it plays a sound and pops up a picture.

Uses the built-in accelerometer on Apple Silicon Macs (M1/M2/M3/M4) to detect physical slaps and respond with a random sound and image from your collection.

---

## Requirements

- MacBook with Apple Silicon (M1, M2, M3, or M4)
- macOS 12 or later
- Python 3.9 or later ([download here](https://www.python.org/downloads/) if needed)

---

## Installation (Fresh Install)

### Step 1 — Download

Download this folder and place it anywhere on your Mac (e.g. your Desktop).

### Step 2 — Add your content

- Drop your sound files (`.mp3`, `.wav`, `.aiff`, `.m4a`, etc.) into the **`sounds/`** folder
- Drop your image files (`.jpg`, `.png`, `.gif`, etc.) into the **`images/`** folder
- *(Optional)* Add a file called **`icon.png`** to the SlapPlayer folder to use as the menu bar icon

### Step 3 — Install

Open **Terminal**, then run:

```bash
cd /path/to/SlapPlayer
./install.sh
```

> **Tip:** You can drag the SlapPlayer folder onto the Terminal window after typing `cd ` to fill in the path automatically.

This installs all the required Python packages into a self-contained virtual environment inside the SlapPlayer folder. It won't affect anything else on your Mac.

### Step 4 — Set up as a background service

```bash
sudo ./setup_background.sh
```

You'll be asked for your Mac password. This installs SlapPlayer as a background service that starts automatically every time you log in.

### Step 5 — Turn it on

Look for the icon in your **menu bar** (top right of your screen). Click it and select **Turn On**. You're ready — slap your Mac!

---

## Usage

| Action | Result |
|--------|--------|
| Slap your Mac | Plays a random sound + shows a random image for 6 seconds |
| Click image | Dismisses it early |
| Menu bar → Turn On/Off | Enables or disables detection |

---

## Adding more content

You can add or swap files in the sounds and images folders at any time. After adding new files, re-run the setup to sync them to the background service:

```bash
sudo ./setup_background.sh
```

---

## Uninstalling

```bash
sudo ./setup_background.sh --uninstall
```

This removes all background services and installed files. The original SlapPlayer folder on your Desktop is untouched.

---

## Troubleshooting

**The menu bar icon doesn't appear**
Make sure the setup completed without errors. Try logging out and back in.

**Slaps aren't being detected**
- Make sure you clicked **Turn On** in the menu bar
- The default sensitivity requires a firm slap — tap the side of your MacBook firmly
- Only works on Apple Silicon Macs (M1/M2/M3/M4), not Intel Macs

**Images aren't showing up**
Make sure there are image files in the `images/` folder and that you re-ran `sudo ./setup_background.sh` after adding them.

**Sounds aren't playing**
Make sure your Mac isn't muted and that there are audio files in the `sounds/` folder.
