#!/usr/bin/env python3
"""
image_popup.py - Shows an image in a borderless popup that auto-closes.
Uses native AppKit (PyObjC) — no tkinter needed.

Usage:
    python3 image_popup.py /path/to/image.jpg
    python3 image_popup.py /path/to/image.jpg --duration 3
"""

import sys
import os
import subprocess
import time
import argparse


def show_with_appkit(image_path, duration):
    """Display image in a native borderless NSWindow using PyObjC."""
    import AppKit
    from Foundation import NSTimer, NSRunLoop, NSDate

    app = AppKit.NSApplication.sharedApplication()
    app.setActivationPolicy_(AppKit.NSApplicationActivationPolicyAccessory)

    # Load image
    ns_image = AppKit.NSImage.alloc().initWithContentsOfFile_(str(image_path))
    if not ns_image:
        raise ValueError(f"Could not load image: {image_path}")

    img_w = ns_image.size().width
    img_h = ns_image.size().height

    # Scale to at most 50% of screen
    screen = AppKit.NSScreen.mainScreen().frame()
    max_w = screen.size.width  * 0.5
    max_h = screen.size.height * 0.5
    scale = min(max_w / img_w, max_h / img_h, 1.0)
    win_w = img_w * scale
    win_h = img_h * scale

    # Center on screen
    x = (screen.size.width  - win_w) / 2
    y = (screen.size.height - win_h) / 2

    # Create borderless window
    rect = AppKit.NSMakeRect(x, y, win_w, win_h)
    style = AppKit.NSWindowStyleMaskBorderless
    window = AppKit.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        rect, style, AppKit.NSBackingStoreBuffered, False
    )
    window.setLevel_(AppKit.NSFloatingWindowLevel)
    window.setBackgroundColor_(AppKit.NSColor.blackColor())
    window.setAlphaValue_(0.95)

    # Add image view
    image_view = AppKit.NSImageView.alloc().initWithFrame_(
        AppKit.NSMakeRect(0, 0, win_w, win_h)
    )
    image_view.setImage_(ns_image)
    image_view.setImageScaling_(AppKit.NSImageScaleAxesIndependently)
    window.contentView().addSubview_(image_view)

    window.makeKeyAndOrderFront_(None)
    app.activateIgnoringOtherApps_(True)

    # Run loop with auto-close after `duration` seconds
    deadline = time.time() + duration
    while time.time() < deadline:
        NSRunLoop.currentRunLoop().runUntilDate_(
            NSDate.dateWithTimeIntervalSinceNow_(0.1)
        )

    window.close()


def show_with_quicklook(image_path, duration):
    """Fallback: open image with Quick Look (qlmanage), close after duration."""
    proc = subprocess.Popen(
        ["qlmanage", "-p", str(image_path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(duration)
    proc.terminate()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", help="Path to the image to show")
    parser.add_argument("--duration", type=int, default=3,
                        help="Seconds before auto-closing (default: 3)")
    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"Image not found: {args.image}")
        sys.exit(1)

    try:
        show_with_appkit(args.image, args.duration)
    except Exception as e:
        print(f"[image_popup] AppKit failed ({e}), trying Quick Look...")
        try:
            show_with_quicklook(args.image, args.duration)
        except Exception as e2:
            print(f"[image_popup] Quick Look also failed: {e2}")
            sys.exit(1)


if __name__ == "__main__":
    main()
