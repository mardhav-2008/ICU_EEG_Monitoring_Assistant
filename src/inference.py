from pathlib import Path

import numpy as np
import pandas as pd
import torch

from model import EEGClassifier


ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "fusion_best.pt"

EEG_SAMPLING_RATE = 200
EEG_WINDOW_SECONDS = 10
EEG_WINDOW_SAMPLES = EEG_SAMPLING_RATE * EEG_WINDOW_SECONDS

SPEC_STEP_SECONDS = 2
SPEC_WINDOW_SECONDS = 120
SPEC_WINDOW_BINS = SPEC_WINDOW_SECONDS // SPEC_STEP_SECONDS

LABELS = [
    "Seizure",
    "GPD",
    "LRDA",
    "Other",
    "GRDA",
    "LPD",
]


device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = EEGClassifier()

checkpoint = torch.load(
    MODEL_PATH,
    map_location=device,
    weights_only=False,
)

model.load_state_dict(checkpoint["model_state_dict"])

model.to(device)
model.eval()


def normalize_channels(data):
    """Normalize each channel independently."""

    mean = data.mean(
        axis=0,
        keepdims=True,
    )

    std = data.std(
        axis=0,
        keepdims=True,
    )

    return (data - mean) / (std + 1e-6)


def prepare_eeg(eeg_path, offset_seconds=0.0):
    """Prepare one EEG window from a parquet file."""

    eeg = pd.read_parquet(eeg_path)

    return prepare_eeg_window(
        eeg.to_numpy(dtype=np.float32),
        offset_seconds,
    )


def prepare_eeg_window(eeg, offset_seconds):
    """Extract and normalize one EEG window."""

    start = int(offset_seconds * EEG_SAMPLING_RATE)

    end = start + EEG_WINDOW_SAMPLES

    data = eeg[start:end]

    if len(data) < EEG_WINDOW_SAMPLES:
        padded = np.zeros(
            (
                EEG_WINDOW_SAMPLES,
                eeg.shape[1],
            ),
            dtype=np.float32,
        )

        padded[: len(data)] = data
        data = padded

    data = np.nan_to_num(data)

    data = normalize_channels(data)

    return torch.from_numpy(data.T.copy()).float()


def get_spectrogram_columns(spectrogram):
    """Return the four spectrogram channel groups."""

    prefixes = [
        "LL_",
        "RL_",
        "LP_",
        "RP_",
    ]

    return [
        [column for column in spectrogram.columns if column.startswith(prefix)]
        for prefix in prefixes
    ]


def prepare_spectrogram(
    spectrogram_path,
    offset_seconds=0.0,
):
    """Prepare one spectrogram window from a parquet file."""

    spectrogram = pd.read_parquet(spectrogram_path)

    columns = get_spectrogram_columns(spectrogram)

    times = spectrogram["time"].to_numpy(dtype=np.float32)

    data = np.stack(
        [spectrogram[group].to_numpy(dtype=np.float32) for group in columns],
        axis=0,
    )

    return prepare_spectrogram_window(
        data,
        times,
        offset_seconds,
    )


def prepare_spectrogram_window(
    spectrogram,
    times,
    offset_seconds,
):
    """Extract and normalize one spectrogram window."""

    start = offset_seconds - SPEC_WINDOW_SECONDS / 2

    end = offset_seconds + SPEC_WINDOW_SECONDS / 2

    start_index = np.searchsorted(
        times,
        start,
        side="left",
    )

    end_index = np.searchsorted(
        times,
        end,
        side="left",
    )

    window = spectrogram[
        :,
        start_index:end_index,
        :,
    ]

    output = np.zeros(
        (
            4,
            SPEC_WINDOW_BINS,
            100,
        ),
        dtype=np.float32,
    )

    length = min(
        window.shape[1],
        SPEC_WINDOW_BINS,
    )

    output[:, :length, :] = window[:, :length, :]

    output = np.nan_to_num(
        output,
        copy=False,
    )

    for channel in range(4):
        mean = output[channel].mean()
        std = output[channel].std()

        output[channel] = (output[channel] - mean) / (std + 1e-6)

    return torch.from_numpy(output).float()


def run_model(eeg, spectrogram):
    """Run the fusion model and return prediction probabilities."""

    eeg = eeg.unsqueeze(0).to(device)
    spectrogram = spectrogram.unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(
            eeg,
            spectrogram,
        )

        probabilities = torch.softmax(
            output,
            dim=1,
        )[0]

    predicted_class = int(torch.argmax(probabilities).item())

    return (
        LABELS[predicted_class],
        probabilities.cpu().numpy(),
    )


def predict(
    eeg_path,
    spectrogram_path,
    eeg_offset_seconds=0.0,
    spectrogram_offset_seconds=0.0,
):
    """
    Run inference on one EEG/spectrogram window.

    This function is kept compatible with assistant.py.
    """

    eeg = prepare_eeg(
        eeg_path,
        eeg_offset_seconds,
    )

    spectrogram = prepare_spectrogram(
        spectrogram_path,
        spectrogram_offset_seconds,
    )

    return run_model(
        eeg,
        spectrogram,
    )


def load_recording(
    eeg_path,
    spectrogram_path,
):
    """
    Load a recording once for repeated monitoring inference.

    Returns NumPy arrays so the monitoring loop does not
    repeatedly read parquet files or scan DataFrames.
    """

    eeg_df = pd.read_parquet(eeg_path)
    spectrogram_df = pd.read_parquet(spectrogram_path)

    eeg = eeg_df.to_numpy(dtype=np.float32)

    columns = get_spectrogram_columns(spectrogram_df)

    times = spectrogram_df["time"].to_numpy(dtype=np.float32)

    spectrogram = np.stack(
        [spectrogram_df[group].to_numpy(dtype=np.float32) for group in columns],
        axis=0,
    )

    return eeg, spectrogram, times


def predict_loaded(
    eeg,
    spectrogram,
    spectrogram_times,
    offset_seconds,
):
    """
    Run inference using recordings already loaded into memory.
    """

    eeg_window = prepare_eeg_window(
        eeg,
        offset_seconds,
    )

    spectrogram_window = prepare_spectrogram_window(
        spectrogram,
        spectrogram_times,
        offset_seconds,
    )

    return run_model(
        eeg_window,
        spectrogram_window,
    )


def get_eeg_duration(eeg_path):
    """Return the EEG recording duration in seconds."""

    num_samples = len(
        pd.read_parquet(
            eeg_path,
            columns=[],
        )
    )

    return num_samples / EEG_SAMPLING_RATE


if __name__ == "__main__":
    print(f"Using device: {device}")

    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")

    validation_accuracy = checkpoint.get("best_val_accuracy")

    if validation_accuracy is not None:
        print(f"Loaded model with validation accuracy: {validation_accuracy:.4f}")
