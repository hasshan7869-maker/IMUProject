"""
IMU Movement Classifier Pipeline
-----------------------------------
Loads labeled CSV files (walk_*.csv, jog_*.csv, jump_*.csv, sprint_*.csv),
slices each into overlapping windows, extracts features per window,
trains a Random Forest classifier, and reports accuracy.

Usage:
    python train_classifier.py

Expects files in the current folder matching: <action>_*.csv
Recognized actions: walk, jog, sprint, jump, cut, kick
(cut/kick will just be picked up automatically once you add them later)
"""

import glob
import os
import re
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

# ---- Settings ----
WINDOW_SIZE = 50       # samples per window (~1s at 50Hz, ~2.5s at 20Hz -- adjust to your actual rate)
WINDOW_STEP = 25        # overlap step (50% overlap)
KNOWN_ACTIONS = ["walk", "jog", "sprint", "jump", "cut", "kick"]
# -------------------

def load_labeled_files():
    """Find all CSVs matching <action>_*.csv and load them with labels."""
    all_data = []

    for action in KNOWN_ACTIONS:
        files = glob.glob(f"{action}_*.csv")
        for filepath in files:
            df = load_csv(filepath)
            if df is None or len(df) == 0:
                continue
            df["label"] = action
            df["source_file"] = os.path.basename(filepath)
            all_data.append(df)
            print(f"Loaded {len(df):4d} samples from {filepath}  ->  label: {action}")

    if not all_data:
        return None

    return pd.concat(all_data, ignore_index=True)


def load_csv(filepath):
    """Load a single IMU CSV, skipping any preamble lines before the header."""
    with open(filepath, "r") as f:
        lines = f.readlines()

    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("timestamp_ms"):
            header_idx = i
            break

    if header_idx is None:
        print(f"Warning: no header found in {filepath}, skipping.")
        return None

    df = pd.read_csv(filepath, skiprows=header_idx)
    df["accel_mag"] = np.sqrt(df["accelX"]**2 + df["accelY"]**2 + df["accelZ"]**2)
    df["gyro_mag"] = np.sqrt(df["gyroX"]**2 + df["gyroY"]**2 + df["gyroZ"]**2)
    return df


def extract_features(window):
    """Turn a window (DataFrame slice) into a single feature row."""
    features = {}

    for col in ["accelX", "accelY", "accelZ", "gyroX", "gyroY", "gyroZ", "accel_mag", "gyro_mag"]:
        values = window[col].values
        features[f"{col}_mean"] = np.mean(values)
        features[f"{col}_std"] = np.std(values)
        features[f"{col}_min"] = np.min(values)
        features[f"{col}_max"] = np.max(values)
        features[f"{col}_range"] = np.max(values) - np.min(values)

    # Zero-crossing rate on accelX as a rough rhythm indicator
    accelX = window["accelX"].values
    zero_crossings = np.sum(np.diff(np.sign(accelX - np.mean(accelX))) != 0)
    features["accelX_zero_crossings"] = zero_crossings

    return features


def build_feature_table(df):
    """Slice each source file into overlapping windows and extract features."""
    rows = []

    for source_file, group in df.groupby("source_file"):
        group = group.reset_index(drop=True)
        label = group["label"].iloc[0]

        for start in range(0, len(group) - WINDOW_SIZE, WINDOW_STEP):
            window = group.iloc[start:start + WINDOW_SIZE]
            features = extract_features(window)
            features["label"] = label
            features["source_file"] = source_file
            rows.append(features)

    return pd.DataFrame(rows)


def main():
    print("Scanning for labeled files...\n")
    raw_df = load_labeled_files()

    if raw_df is None:
        print("\nNo labeled files found. Make sure files are named like walk_01.csv, jog_01.csv, etc.")
        return

    print(f"\nTotal raw samples loaded: {len(raw_df)}")
    print(f"Classes found: {sorted(raw_df['label'].unique())}\n")

    print("Building feature table (windowing)...")
    feature_df = build_feature_table(raw_df)
    print(f"Total windows extracted: {len(feature_df)}")
    print(feature_df["label"].value_counts())
    print()

    if len(feature_df) < 20:
        print("Not enough windows yet to train a meaningful classifier.")
        print("Record more trials per action and try again.")
        return

    # Prepare features/labels
    feature_cols = [c for c in feature_df.columns if c not in ("label", "source_file")]
    X = feature_df[feature_cols]
    y = feature_df["label"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    print(f"Training on {len(X_train)} windows, testing on {len(X_test)} windows...\n")

    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)

    print("=== Classification Report ===")
    print(classification_report(y_test, y_pred))

    print("=== Confusion Matrix ===")
    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    print("Rows = actual, Columns = predicted")
    print("Labels order:", labels)
    print(cm)

    print("\n=== Top 10 Most Important Features ===")
    importances = pd.Series(clf.feature_importances_, index=feature_cols)
    print(importances.sort_values(ascending=False).head(10))


if __name__ == "__main__":
    main()
