from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DATA = ROOT / "data" / "raw"
OUTPUTS = ROOT / "outputs"
PROCESSED = ROOT / "data" / "processed"

TRAIN_EEG_DIR = RAW_DATA / "train_eegs"

WINDOW_SECONDS = 10
SAMPLING_RATE = 200
WINDOW_SAMPLES = WINDOW_SECONDS * SAMPLING_RATE

LABEL_MAP = {
    "Seizure": 0,
    "GPD": 1,
    "LRDA": 2,
    "Other": 3,
    "GRDA": 4,
    "LPD": 5,
}


PROCESSED.mkdir(parents=True, exist_ok=True)


def prepare_split(df, name):
    n_samples = len(df)
    n_channels = 20

    data_path = PROCESSED / f"{name}_x.npy"
    labels_path = PROCESSED / f"{name}_y.npy"

    x = np.lib.format.open_memmap(
        data_path,
        mode="w+",
        dtype=np.float16,
        shape=(n_samples, n_channels, WINDOW_SAMPLES),
    )

    y = np.lib.format.open_memmap(
        labels_path,
        mode="w+",
        dtype=np.int64,
        shape=(n_samples,),
    )

    grouped = df.groupby("eeg_id", sort=False)

    processed = 0

    for eeg_id, group in grouped:
        eeg_path = TRAIN_EEG_DIR / f"{int(eeg_id)}.parquet"

        eeg = pd.read_parquet(eeg_path)

        signal = eeg.to_numpy(dtype=np.float32)

        for index, row in group.iterrows():
            offset = int(float(row["eeg_label_offset_seconds"]) * SAMPLING_RATE)

            window = signal[offset : offset + WINDOW_SAMPLES]

            if window.shape[0] < WINDOW_SAMPLES:
                padding = WINDOW_SAMPLES - window.shape[0]

                window = np.pad(
                    window,
                    ((0, padding), (0, 0)),
                    mode="constant",
                )

            window = np.nan_to_num(
                window,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )

            mean = window.mean(axis=0, keepdims=True)
            std = window.std(axis=0, keepdims=True)

            window = (window - mean) / (std + 1e-6)

            window = window.T

            position = df.index.get_loc(index)

            x[position] = window.astype(np.float16)

            y[position] = LABEL_MAP[row["expert_consensus"]]

            processed += 1

        if processed % 1000 == 0:
            print(f"{name}: {processed}/{n_samples}")

    x.flush()
    y.flush()

    print(f"\nFinished {name}")
    print(f"Data: {data_path}")
    print(f"Labels: {labels_path}")


train_df = pd.read_csv(OUTPUTS / "train_split.csv")
val_df = pd.read_csv(OUTPUTS / "val_split.csv")

prepare_split(train_df, "train")
prepare_split(val_df, "val")
