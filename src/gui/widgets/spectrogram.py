from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class SpectrogramWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)

        self.title = QLabel("SPECTROGRAM  /  WAITING FOR RECORDING")
        self.title.setObjectName("fieldLabel")
        layout.addWidget(self.title)

        self.image = pg.ImageView()
        self.image.ui.roiBtn.hide()
        self.image.ui.menuBtn.hide()
        self.image.getView().setBackgroundColor("#0a1c24")
        layout.addWidget(self.image)

    def clear(self):
        self.image.clear()
        self.title.setText("SPECTROGRAM  /  WAITING FOR RECORDING")

    def set_spectrogram(self, data):
        array = np.asarray(data, dtype=np.float32)

        if array.ndim == 3 and array.shape[0] == 4:
            # Four groups (LL/RL/LP/RP), average for a compact overview.
            image = np.mean(array, axis=0).T
        elif array.ndim == 2:
            image = array.T
        else:
            raise ValueError(f"Unexpected spectrogram shape: {array.shape}")

        image = np.nan_to_num(image, nan=0.0, posinf=0.0, neginf=0.0)
        self.image.setImage(image, autoLevels=True)
        self.title.setText(f"SPECTROGRAM  /  MODEL INPUT  ·  {array.shape}")
