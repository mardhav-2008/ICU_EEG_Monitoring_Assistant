from pathlib import Path
import json
import time

import joblib
import numpy as np
import pandas as pd
from scipy.signal import welch
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs"
FEATURE_DIR = OUTPUTS / "features"
MODEL_DIR = ROOT / "models"

FEATURE_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

LABELS = [
    "Seizure",
    "GPD",
    "LRDA",
    "Other",
    "GRDA",
    "LPD",
]

FS = 200
BATCH_SIZE = 128

BANDS = {
    "delta": (0.5, 4.0),
    "theta": (4.0, 8.0),
    "alpha": (8.0, 13.0),
    "beta": (13.0, 30.0),
    "gamma": (30.0, 45.0),
}


def extract_features(split):
    feature_path = FEATURE_DIR / f"{split}_bandpower_v1.npy"

    if feature_path.exists():
        print(f"Using cached {split} features: {feature_path}")
        return np.load(feature_path, mmap_mode="r")

    eeg_path = PROCESSED / f"{split}_x.npy"
    eeg = np.load(eeg_path, mmap_mode="r")

    n_samples, n_channels, _ = eeg.shape

    print(f"\nExtracting {split} features")
    print("EEG shape:", eeg.shape)

    features = np.lib.format.open_memmap(
        feature_path,
        mode="w+",
        dtype=np.float32,
        shape=(n_samples, n_channels * len(BANDS)),
    )

    for start in range(0, n_samples, BATCH_SIZE):
        end = min(start + BATCH_SIZE, n_samples)

        batch = np.asarray(eeg[start:end], dtype=np.float32)

        freqs, psd = welch(
            batch,
            fs=FS,
            window="hann",
            nperseg=400,
            noverlap=200,
            axis=-1,
            scaling="density",
        )

        total_mask = (freqs >= 0.5) & (freqs <= 45.0)

        total_power = np.trapezoid(
            psd[..., total_mask],
            x=freqs[total_mask],
            axis=-1,
        )

        sample_features = []

        for low, high in BANDS.values():
            mask = (freqs >= low) & (freqs <= high)

            band_power = np.trapezoid(
                psd[..., mask],
                x=freqs[mask],
                axis=-1,
            )

            relative_power = band_power / (total_power + 1e-12)
            sample_features.append(relative_power)

        # (batch, channels, bands)
        sample_features = np.stack(sample_features, axis=-1)

        # (batch, channels * bands)
        features[start:end] = sample_features.reshape(end - start, -1)

        if end % 4096 == 0 or end == n_samples:
            print(f"{split}: {end}/{n_samples}")

    features.flush()

    print("Saved:", feature_path)

    return np.load(feature_path, mmap_mode="r")


def main():
    start_time = time.time()

    print("ICU EEG - Band Power Random Forest")
    print("=" * 55)

    X_train = extract_features("train")
    X_val = extract_features("val")

    y_train = np.load(PROCESSED / "train_y.npy")
    y_val = np.load(PROCESSED / "val_y.npy")

    print("\nFeature shapes:")
    print("Training:", X_train.shape)
    print("Validation:", X_val.shape)

    print("\nTraining Random Forest...")

    model = RandomForestClassifier(
        n_estimators=200,
        max_features="sqrt",
        min_samples_leaf=2,
        class_weight="balanced_subsample",
        random_state=42,
        n_jobs=-1,
        verbose=1,
    )

    model.fit(X_train, y_train)

    print("\nEvaluating...")

    predictions = model.predict(X_val)

    accuracy = accuracy_score(y_val, predictions)
    balanced_accuracy = balanced_accuracy_score(y_val, predictions)
    macro_f1 = f1_score(y_val, predictions, average="macro")
    weighted_f1 = f1_score(y_val, predictions, average="weighted")

    print("\nClassification Report\n")

    report = classification_report(
        y_val,
        predictions,
        labels=list(range(6)),
        target_names=LABELS,
        digits=4,
        zero_division=0,
    )

    print(report)

    print("Accuracy:", accuracy)
    print("Balanced accuracy:", balanced_accuracy)
    print("Macro F1:", macro_f1)
    print("Weighted F1:", weighted_f1)

    cm = confusion_matrix(y_val, predictions, labels=list(range(6)))

    print("\nConfusion Matrix")
    print(pd.DataFrame(cm, index=LABELS, columns=LABELS))

    # Save model
    model_path = MODEL_DIR / "band_power_random_forest.joblib"
    joblib.dump(model, model_path)

    # Save metrics
    metrics = {
        "model": "Band Power Random Forest",
        "n_estimators": 200,
        "max_features": "sqrt",
        "min_samples_leaf": 2,
        "class_weight": "balanced_subsample",
        "random_state": 42,
        "training_samples": len(y_train),
        "validation_samples": len(y_val),
        "features_per_sample": X_train.shape[1],
        "accuracy": accuracy,
        "balanced_accuracy": balanced_accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
    }

    metrics_path = OUTPUTS / "random_forest_metrics.json"

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=4)

    # Save classification report and confusion matrix
    report_dict = classification_report(
        y_val,
        predictions,
        labels=list(range(6)),
        target_names=LABELS,
        output_dict=True,
        zero_division=0,
    )

    pd.DataFrame(report_dict).transpose().to_csv(
        OUTPUTS / "random_forest_classification_report.csv"
    )

    pd.DataFrame(cm, index=LABELS, columns=LABELS).to_csv(
        OUTPUTS / "random_forest_confusion_matrix.csv"
    )

    print("\nSaved model:", model_path)
    print("Saved metrics:", metrics_path)

    print(f"\nTotal execution time: {(time.time() - start_time) / 60:.2f} minutes")


if __name__ == "__main__":
    main()
