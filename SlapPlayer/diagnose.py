#!/usr/bin/env python3
"""
SlapPlayer Diagnostic v2 - Tests different ways to get accelerometer data.
Usage:  sudo .venv/bin/python3 diagnose.py
"""

import sys
import os
import time
import math

print("=" * 50)
print("  SlapPlayer Diagnostic v2")
print("=" * 50)

if os.geteuid() != 0:
    print("\n[ERROR] Run with sudo:  sudo .venv/bin/python3 diagnose.py")
    sys.exit(1)

from macimu import IMU
imu = IMU()
print(f"[OK] IMU created")

sample_count = 0
max_mag = 0.0

def on_sample(sample):
    global sample_count, max_mag
    sample_count += 1
    try:
        if isinstance(sample, (list, tuple)):
            x, y, z = sample[0], sample[1], sample[2]
        elif hasattr(sample, 'x'):
            x, y, z = sample.x, sample.y, sample.z
        else:
            if sample_count <= 3:
                print(f"    Unknown format: type={type(sample)} val={sample}")
            return
        mag = math.sqrt(x*x + y*y + z*z)
        if mag > max_mag:
            max_mag = mag
        if sample_count % 50 == 0:
            print(f"    [#{sample_count:>5}] x={x:>8.3f} y={y:>8.3f} z={z:>8.3f} mag={mag:.3f}g")
        if mag > 2.0:
            print(f"    *** SLAP *** mag={mag:.3f}g")
    except Exception as e:
        print(f"    Error: {e} | raw={sample}")

# -------------------------------------------------------
# Test 1: on_accel + imu.start()
# -------------------------------------------------------
print("\n[Test 1] on_accel + imu.start()...")
sample_count = 0
imu.on_accel(on_sample)
try:
    imu.start()
    print("    imu.start() called OK")
except Exception as e:
    print(f"    imu.start() error: {e}")

time.sleep(3)
print(f"    Samples after 3s: {sample_count}")
if sample_count > 0:
    print("    SUCCESS! on_accel + start() works.")
    print("\n    Now slap your Mac for 7 more seconds...")
    time.sleep(7)
    print(f"\n    Total samples: {sample_count}, max magnitude: {max_mag:.3f}g")
    sys.exit(0)

try:
    imu.stop()
except:
    pass

# -------------------------------------------------------
# Test 2: Polling with read_accel
# -------------------------------------------------------
print("\n[Test 2] Polling with imu.read_accel()...")
sample_count = 0
try:
    for i in range(30):
        data = imu.read_accel()
        if data is not None:
            sample_count += 1
            if sample_count <= 3 or sample_count % 10 == 0:
                print(f"    read_accel() = {data} (type={type(data)})")
            if isinstance(data, (list, tuple)) and len(data) >= 3:
                mag = math.sqrt(data[0]**2 + data[1]**2 + data[2]**2)
                if mag > max_mag:
                    max_mag = mag
                if mag > 2.0:
                    print(f"    *** SLAP *** mag={mag:.3f}g")
        else:
            if i < 3:
                print(f"    read_accel() returned None")
        time.sleep(0.1)
except Exception as e:
    print(f"    read_accel() error: {e}")

if sample_count > 0:
    print(f"    SUCCESS! Polling works. Got {sample_count} samples.")
    print(f"    Max magnitude: {max_mag:.3f}g")
    sys.exit(0)

# -------------------------------------------------------
# Test 3: stream_accel generator
# -------------------------------------------------------
print("\n[Test 3] imu.stream_accel()...")
sample_count = 0
try:
    stream = imu.stream_accel()
    print(f"    stream type: {type(stream)}")
    start_time = time.time()
    for sample in stream:
        sample_count += 1
        if sample_count <= 3:
            print(f"    stream sample: {sample} (type={type(sample)})")
        if isinstance(sample, (list, tuple)) and len(sample) >= 3:
            mag = math.sqrt(sample[0]**2 + sample[1]**2 + sample[2]**2)
            if mag > max_mag:
                max_mag = mag
            if sample_count % 50 == 0:
                print(f"    [#{sample_count}] mag={mag:.3f}g")
            if mag > 2.0:
                print(f"    *** SLAP *** mag={mag:.3f}g")
        if time.time() - start_time > 5:
            break
except Exception as e:
    print(f"    stream_accel() error: {e}")

if sample_count > 0:
    print(f"    SUCCESS! Streaming works. Got {sample_count} samples.")
    print(f"    Max magnitude: {max_mag:.3f}g")
    sys.exit(0)

# -------------------------------------------------------
# Test 4: read_accel_timed
# -------------------------------------------------------
print("\n[Test 4] imu.read_accel_timed()...")
try:
    for i in range(10):
        data = imu.read_accel_timed()
        print(f"    read_accel_timed() = {data}")
        if data is not None:
            sample_count += 1
        time.sleep(0.2)
except Exception as e:
    print(f"    read_accel_timed() error: {e}")

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
print(f"\n{'=' * 50}")
print(f"  None of the methods returned data.")
print(f"  Try: imu.available = {imu.available}")
try:
    print(f"  Device info: {imu.device_info}")
except:
    print(f"  Device info: (error reading)")
print(f"{'=' * 50}\n")
