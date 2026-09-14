"""
IMU Event Detector
--------------------
Loads a CSV logged by log_imu_data.py and automatically detects
"events" (spikes) in acceleration magnitude and gyro magnitude,
printing their timestamps so you can cross-check them against
what you actually did during that recording.

Usage:
    python detect_events.py imu_log_20260909_143022.csv

If no filename is given, it looks for the most recently modified
imu_log_*.csv file in the current folder.
"""

import sys
import glob
import os
import numpy as np
import pandas as pd
from scipy.signal import find_peaks


def find_latest_csv():
    files = glob.glob("imu_log_*.csv")
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def load_data(filename):
    with open(filename, "r") as f:
        lines = f.readlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("timestamp_ms"):
            header_idx = i
            break

    if header_idx is None:
        raise ValueError("Could not find the CSV header row (timestamp_ms,...) in this file.")

    df = pd.read_csv(filename, skiprows=header_idx)
    df["time_s"] = df["timestamp_ms"] / 1000.0
    df["accel_mag"] = np.sqrt(df["accelX"]**2 + df["accelY"]**2 + df["accelZ"]**2)
    df["gyro_mag"] = np.sqrt(df["gyroX"]**2 + df["gyroY"]**2 + df["gyroZ"]**2)
    return df


def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = find_latest_csv()
        if filename is None:
            print("No CSV file specified and none found in this folder.")
            print("Usage: python detect_events.py <filename.csv>")
            return
        print(f"No filename given — using most recent file: {filename}")

    df = load_data(filename)

    # ---- Tunable thresholds — adjust based on what you see ----
    ACCEL_THRESHOLD_G = 3.0       # accel magnitude above this = event
    GYRO_THRESHOLD_DPS = 300.0    # gyro magnitude above this = event
    MIN_DISTANCE_SAMPLES = 20     # minimum samples between separate peaks
    # -------------------------------------------------------------

    accel_peaks, accel_props = find_peaks(
        df["accel_mag"],
        height=ACCEL_THRESHOLD_G,
        distance=MIN_DISTANCE_SAMPLES
    )

    gyro_peaks, gyro_props = find_peaks(
        df["gyro_mag"],
        height=GYRO_THRESHOLD_DPS,
        distance=MIN_DISTANCE_SAMPLES
    )

    print(f"\nLoaded {len(df)} samples spanning {df['time_s'].iloc[-1]:.2f} seconds\n")

    print(f"=== Acceleration events (threshold: {ACCEL_THRESHOLD_G}g) ===")
    if len(accel_peaks) == 0:
        print("No events found. Try lowering ACCEL_THRESHOLD_G.")
    else:
        for idx, peak_val in zip(accel_peaks, accel_props["peak_heights"]):
            t = df["time_s"].iloc[idx]
            print(f"  t = {t:6.2f}s   |   peak magnitude = {peak_val:.2f}g")

    print(f"\n=== Gyro events (threshold: {GYRO_THRESHOLD_DPS} dps) ===")
    if len(gyro_peaks) == 0:
        print("No events found. Try lowering GYRO_THRESHOLD_DPS.")
    else:
        for idx, peak_val in zip(gyro_peaks, gyro_props["peak_heights"]):
            t = df["time_s"].iloc[idx]
            print(f"  t = {t:6.2f}s   |   peak magnitude = {peak_val:.0f} dps")

    print("\nCompare these timestamps against what you remember doing during the recording.")
    print("Adjust ACCEL_THRESHOLD_G / GYRO_THRESHOLD_DPS at the top of this script if")
    print("events are missing or too many false ones show up.")


if __name__ == "__main__":
    main()
