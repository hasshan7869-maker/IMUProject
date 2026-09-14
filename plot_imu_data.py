"""
IMU Data Plotter
-----------------
Loads a CSV logged by log_imu_data.py and plots:
  1. Accelerometer X/Y/Z over time
  2. Gyroscope X/Y/Z over time
  3. Acceleration magnitude (orientation-independent) over time

Usage:
    python plot_imu_data.py imu_log_20260909_143022.csv

If no filename is given, it looks for the most recently modified
imu_log_*.csv file in the current folder.
"""

import sys
import glob
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def find_latest_csv():
    files = glob.glob("imu_log_*.csv")
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def main():
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = find_latest_csv()
        if filename is None:
            print("No CSV file specified and none found in this folder.")
            print("Usage: python plot_imu_data.py <filename.csv>")
            return
        print(f"No filename given — using most recent file: {filename}")

    # The first line in the file is the sketch's startup message,
    # then a header row, then data. Skip lines until we hit the real header.
    with open(filename, "r") as f:
        lines = f.readlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("timestamp_ms"):
            header_idx = i
            break

    if header_idx is None:
        print("Could not find the CSV header row (timestamp_ms,...) in this file.")
        print("Check that the file contains the expected serial output.")
        return

    df = pd.read_csv(filename, skiprows=header_idx)

    # Convert timestamp from ms to seconds for readability
    df["time_s"] = df["timestamp_ms"] / 1000.0

    # Compute acceleration magnitude (orientation-independent)
    df["accel_mag"] = np.sqrt(df["accelX"]**2 + df["accelY"]**2 + df["accelZ"]**2)

    # Compute gyro magnitude too, useful for direction-change/cut detection
    df["gyro_mag"] = np.sqrt(df["gyroX"]**2 + df["gyroY"]**2 + df["gyroZ"]**2)

    print(f"Loaded {len(df)} samples spanning {df['time_s'].iloc[-1]:.2f} seconds")

    fig, axes = plt.subplots(4, 1, figsize=(12, 10), sharex=True)

    # Accel X/Y/Z
    axes[0].plot(df["time_s"], df["accelX"], label="X")
    axes[0].plot(df["time_s"], df["accelY"], label="Y")
    axes[0].plot(df["time_s"], df["accelZ"], label="Z")
    axes[0].set_ylabel("Accel (g)")
    axes[0].set_title("Accelerometer")
    axes[0].legend(loc="upper right")
    axes[0].grid(True, alpha=0.3)

    # Gyro X/Y/Z
    axes[1].plot(df["time_s"], df["gyroX"], label="X")
    axes[1].plot(df["time_s"], df["gyroY"], label="Y")
    axes[1].plot(df["time_s"], df["gyroZ"], label="Z")
    axes[1].set_ylabel("Gyro (dps)")
    axes[1].set_title("Gyroscope")
    axes[1].legend(loc="upper right")
    axes[1].grid(True, alpha=0.3)

    # Accel magnitude
    axes[2].plot(df["time_s"], df["accel_mag"], color="tab:red")
    axes[2].axhline(1.0, color="gray", linestyle="--", alpha=0.5, label="1g (at rest)")
    axes[2].set_ylabel("Accel mag (g)")
    axes[2].set_title("Acceleration Magnitude (spikes = impacts/jumps/sprints)")
    axes[2].legend(loc="upper right")
    axes[2].grid(True, alpha=0.3)

    # Gyro magnitude
    axes[3].plot(df["time_s"], df["gyro_mag"], color="tab:purple")
    axes[3].set_ylabel("Gyro mag (dps)")
    axes[3].set_xlabel("Time (s)")
    axes[3].set_title("Gyro Magnitude (spikes = direction changes/rotation)")
    axes[3].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
