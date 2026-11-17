from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class SpectrogramWidget(QFrame):
    """Dark, minimal spectrogram with no histogram side panel."""

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(8)

        self.title = QLabel("SPECTROGRAM  /  WAITING FOR RECORDING")
        self.title.setObjectName("fieldLabel")
        layout.addWidget(self.title)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#101D20")
        self.plot.showGrid(x=True, y=True, alpha=0.12)
        self.plot.setLabel("bottom", "Time bins", color="#9AAFA3")
        self.plot.setLabel("left", "Frequency bins", color="#9AAFA3")
        for axis_name in ("bottom", "left"):
            axis = self.plot.getAxis(axis_name)
            axis.setTextPen("#9AAFA3")
            axis.setPen("#53665C")
        self.plot.getPlotItem().hideButtons()
        self.plot.getPlotItem().setMenuEnabled(False)

        self.image = pg.ImageItem()
        self.image.setOpts(axisOrder="row-major")
        self.plot.addItem(self.image)
        self.plot.setAspectLocked(False)
        layout.addWidget(self.plot)

    def clear(self):
        self.image.clear()
        self.title.setText("SPECTROGRAM  /  WAITING FOR RECORDING")

    def set_spectrogram(self, data):
        array = np.asarray(data, dtype=np.float32)
        if array.ndim == 3 and array.shape[0] == 4:
            image = np.mean(array, axis=0).T
        elif array.ndim == 2:
            image = array.T
        else:
            raise ValueError(f"Unexpected spectrogram shape: {array.shape}")

        image = np.nan_to_num(image, nan=0.0, posinf=0.0, neginf=0.0)
        self.image.setImage(image, autoLevels=True)
        self.image.setLookupTable(self._sage_lut())
        height, width = image.shape
        self.plot.setXRange(0, width, padding=0)
        self.plot.setYRange(0, height, padding=0)
        self.title.setText(f"SPECTROGRAM  /  MODEL INPUT  ·  {array.shape}")

    @staticmethod
    def _sage_lut():
        stops = np.array([
            [0.00, 0.025, 0.055, 0.060],
            [0.28, 0.19, 0.31, 0.26],
            [0.55, 0.38, 0.54, 0.42],
            [0.78, 0.64, 0.70, 0.48],
            [1.00, 0.84, 0.68, 0.43],
        ])
        x = np.linspace(0, 1, 256)
        lut = np.stack(
            [np.interp(x, stops[:, 0], stops[:, i]) for i in range(1, 4)],
            axis=1
        )
        return np.clip(lut * 255, 0, 255).astype(np.ubyte)
