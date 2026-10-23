from pathlib import Path

import numpy as np
import torch
from torch.utils.data import Dataset


ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"


LABEL_MAP = {
    "Seizure": 0,
    "GPD": 1,
    "LRDA": 2,
    "Other": 3,
    "GRDA": 4,
    "LPD": 5,
}

ID_TO_LABEL = {value: key for key, value in LABEL_MAP.items()}


class EEGDataset(Dataset):
    def __init__(self, split):

        self.eeg = np.load(PROCESSED / f"{split}_x.npy", mmap_mode="r")

        self.spectrogram = np.load(PROCESSED / f"{split}_spec_x.npy", mmap_mode="r")

        self.labels = np.load(PROCESSED / f"{split}_y.npy", mmap_mode="r")

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, index):

        eeg = torch.from_numpy(self.eeg[index].copy()).float()

        spectrogram = torch.from_numpy(self.spectrogram[index].copy()).float()

        label = torch.tensor(self.labels[index], dtype=torch.long)

        return eeg, spectrogram, label
