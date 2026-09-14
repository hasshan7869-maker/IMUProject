"""
nRF Connect Log Parser
------------------------
Converts a .txt log exported from nRF Connect (phone app) into the
same CSV format used by the wired/BLE-laptop loggers, so it drops
straight into plot_imu_data.py and detect_events.py unchanged.

Usage:
    python parse_nrf_log.py Log_2026-09-10_21_34_41.txt
"""

import sys
import re
import struct
import os

# Must match the ImuPacket struct in the .ino sketch
PACKET_FORMAT = "<Ihhhhhh"
PACKET_SIZE = struct.calcsize(PACKET_FORMAT)  # 16 bytes

# Matches lines like:
# I    21:34:27.389    Notification received from beb5483e-...-a8, value: (0x) 2F-40-00-00-CB-FF-45-00-EF-03-D0-FF-F5-FF-3E-FF
NOTIFICATION_PATTERN = re.compile(
    r"Notification received from [0-9a-fA-F\-]+, value: \(0x\) ([0-9A-Fa-f\-]+)"
)


def hex_string_to_bytes(hex_str):
    # "2F-40-00-00-CB-FF..." -> bytes
    parts = hex_str.strip().split("-")
    return bytes(int(p, 16) for p in parts)


def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_nrf_log.py <log_file.txt>")
        return

    input_file = sys.argv[1]

    if not os.path.exists(input_file):
        print(f"File not found: {input_file}")
        return

    base_name = os.path.splitext(os.path.basename(input_file))[0]
    output_file = f"imu_log_nrf_{base_name}.csv"

    rows_written = 0
    skipped = 0

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f_in, \
         open(output_file, "w", newline="") as f_out:

        f_out.write("timestamp_ms,accelX,accelY,accelZ,gyroX,gyroY,gyroZ\n")

        for line in f_in:
            match = NOTIFICATION_PATTERN.search(line)
            if not match:
                continue

            hex_str = match.group(1)

            try:
                packet_bytes = hex_string_to_bytes(hex_str)
            except ValueError:
                skipped += 1
                continue

            if len(packet_bytes) != PACKET_SIZE:
                # Skip anything that isn't a full IMU packet
                # (e.g. the Client Characteristic Configuration write, etc.)
                skipped += 1
                continue

            timestamp_ms, ax_mg, ay_mg, az_mg, gx10, gy10, gz10 = struct.unpack(
                PACKET_FORMAT, packet_bytes
            )

            accelX = ax_mg / 1000.0
            accelY = ay_mg / 1000.0
            accelZ = az_mg / 1000.0
            gyroX = gx10 / 10.0
            gyroY = gy10 / 10.0
            gyroZ = gz10 / 10.0

            f_out.write(
                f"{timestamp_ms},{accelX:.4f},{accelY:.4f},{accelZ:.4f},"
                f"{gyroX:.3f},{gyroY:.3f},{gyroZ:.3f}\n"
            )
            rows_written += 1

    print(f"Parsed {rows_written} IMU packets from {input_file}")
    if skipped:
        print(f"Skipped {skipped} non-IMU-packet lines (expected, e.g. config writes)")
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()
