# Soccer Motion-Tracking Wearable (IMU)

A wireless, untethered motion-capture system built around an ESP32 and IMU, aimed at tracking soccer-specific movement (sprints, cuts, jumps, kicks) in real time. This is the first stage of a planned multisensor athletic wearable.

## Overview

This project streams live accelerometer/gyroscope data from a body-worn sensor to a receiving device over Bluetooth Low Energy, with a Python-based pipeline for logging, visualizing, and automatically detecting movement events.

**Hardware:** ESP32-WROOM-32E + BMI270 IMU breakout (I2C)
**Firmware:** Arduino IDE / ESP32 core, BLE (ESP32 built-in library)
**Host tooling:** Python (pyserial, scipy)

## Hardware & Sensor Configuration

- ESP32-WROOM-32E connected to a BMI270 IMU breakout over I2C (3.3V, GND, SDA, SCL)
- BMI270 configured for **±16g accelerometer range** and **±2000°/s gyroscope range** — wide enough to avoid saturation during sprints, jumps, and cuts
- I2C link verified via a WHO_AM_I-style identity check using the SparkFun BMI270 Arduino library

## Data Pipeline (Wired Prototype)

Before going wireless, the system was validated over a wired USB serial connection:

- Python (`pyserial`) script logs the raw CSV stream to timestamped files
- Plotting script visualizes accel/gyro over time, plus accel/gyro magnitude
- Peak-detection script (`scipy.signal.find_peaks`) auto-flags events crossing accel/gyro thresholds

## Going Wireless: BLE Streaming

Switched to BLE using the ESP32's built-in BLE library, sending compact **16-byte binary packets** (scaled integers rather than floats/text) to fit cleanly within the default BLE packet size.

### The packet-loss problem

At a 50 Hz send rate, only **~7.6%** of packets were arriving at the receiver. Rather than assuming a code bug, a send-side counter confirmed the ESP32 was reliably transmitting at the full 50 Hz — meaning the bottleneck was downstream, not in the firmware.

### Root cause and fix

The actual bottleneck was the **BLE connection interval** — the negotiated timing window between the two devices, which by default was far too coarse for a 50 Hz stream. Explicitly requesting a faster connection interval on connect improved effective throughput to **~36.7%** in live, fully untethered field testing (board running on battery, no laptop cable).

### Further improvement: switching the receiver to a phone

Receiving on a phone (via nRF Connect) instead of a laptop pushed effective throughput to **over 90%**, benefiting from a faster negotiated connection, larger supported data payload, and generally faster BLE radio handling on Android.

## First Real Motion Data

Captured fully untethered sessions covering jogging, jumping, accelerating, and kicking. Event detection produced clear, distinguishable signatures for different movement types (jog vs. jump/kick vs. sprint-like bursts).

![Motion capture results]([images/motion_capture_results.png](https://github.com/hasshan7869-maker/IMUProject/blob/47444056b9109e50e63ce09ba514b8ce2ef540ee/Screenshot%202026-09-13%20104011.png))

## Enclosure

Designed a custom enclosure in SolidWorks, sized and constrained around the ESP32 + BMI270 board footprint. CAD is complete; not yet 3D printed.

![Enclosure design]([images/enclosure_render.png](https://github.com/hasshan7869-maker/IMUProject/blob/47444056b9109e50e63ce09ba514b8ce2ef540ee/Screenshot%202026-09-13%20091618.png))

## Tech Stack

- ESP32-WROOM-32E, BMI270 IMU
- Arduino IDE (ESP32 board support, CP210x USB driver)
- ESP32 built-in BLE library
- Python: `pyserial`, `scipy`, `matplotlib` (or similar) for logging/plotting/event detection
- SolidWorks (enclosure design)

## Current Status / Next Steps

- [x] Wired IMU acquisition + logging/plotting/event detection pipeline
- [x] BLE streaming with diagnosed and resolved packet-loss bottleneck
- [x] Fully untethered live motion capture with working event detection
- [x] Enclosure designed in SolidWorks (not yet printed)
- [ ] Record a labeled six-class dataset (walk, jog, sprint, jump, cut, kick) with clean reps and rest-gaps
- [ ] Windowing / feature extraction for the labeled dataset
- [ ] Train a movement classifier
- [ ] Speed/direction estimation (flagged as a hard problem — raw accel integration drifts significantly without correction)
- [ ] 3D print and mount the enclosure
- [ ] Expand to a full multisensor system: add PPG (heart rate) and temperature sensing
- [ ] Battery integration for a standalone wearable

## Background

Built as a step toward a multisensor athletic performance wearable, combining motion tracking with future physiological sensing (heart rate, temperature) for a more complete picture of athlete workload and movement quality.
