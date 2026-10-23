from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

RAW_DATA = ROOT / "data" / "raw"
OUTPUTS = ROOT / "outputs"
PROCESSED = ROOT / "data" / "processed"

SPECTROGRAM_DIR = RAW_DATA / "train_spectrograms"


WINDOW_SECONDS = 120
TIME_STEP = 2
WINDOW_BINS = WINDOW_SECONDS // TIME_STEP

FREQUENCY_BINS = 100

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

    data_path = PROCESSED / f"{name}_spec_x.npy"

    x = np.lib.format.open_memmap(
        data_path,
        mode="w+",
        dtype=np.float16,
        shape=(n_samples, 4, WINDOW_BINS, FREQUENCY_BINS),
    )

    grouped = df.groupby("spectrogram_id", sort=False)

    processed = 0

    for spectrogram_id, group in grouped:
        spectrogram_path = SPECTROGRAM_DIR / f"{int(spectrogram_id)}.parquet"

        spectrogram = pd.read_parquet(spectrogram_path)

        times = spectrogram["time"].to_numpy()

        channels = []

        for prefix in ["LL_", "RL_", "LP_", "RP_"]:
            columns = [
                column for column in spectrogram.columns if column.startswith(prefix)
            ]

            columns = sorted(columns, key=lambda column: float(column.split("_")[1]))

            channels.append(spectrogram[columns].to_numpy(dtype=np.float32))

        spectrogram = np.stack(channels, axis=0)

        for index, row in group.iterrows():
            label_time = float(row["spectrogram_label_offset_seconds"])

            center = np.argmin(np.abs(times - label_time))

            start = center - WINDOW_BINS // 2
            end = start + WINDOW_BINS

            window = np.zeros(
                (4, WINDOW_BINS, FREQUENCY_BINS),
                dtype=np.float32,
            )

            source_start = max(start, 0)
            source_end = min(end, len(times))

            target_start = source_start - start
            target_end = target_start + (source_end - source_start)

            window[:, target_start:target_end, :] = spectrogram[
                :, source_start:source_end, :
            ]

            window = np.nan_to_num(
                window,
                nan=0.0,
                posinf=0.0,
                neginf=0.0,
            )

            mean = window.mean(axis=(1, 2), keepdims=True)

            std = window.std(axis=(1, 2), keepdims=True)

            window = (window - mean) / (std + 1e-6)

            position = df.index.get_loc(index)

            x[position] = window.astype(np.float16)

            processed += 1

        if processed % 1000 == 0:
            print(f"{name}: {processed}/{n_samples}")

    x.flush()

    print()
    print(f"Finished {name}")
    print(f"Data: {data_path}")


train_df = pd.read_csv(OUTPUTS / "train_split.csv")

val_df = pd.read_csv(OUTPUTS / "val_split.csv")

train_df = train_df.reset_index(drop=True)
val_df = val_df.reset_index(drop=True)

prepare_split(train_df, "train")
prepare_split(val_df, "val")
