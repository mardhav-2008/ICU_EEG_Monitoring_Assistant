from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QEasingCurve, QVariantAnimation, Qt
from PySide6.QtWidgets import QFrame, QLabel, QStackedLayout, QVBoxLayout, QWidget


class SpectrogramWidget(QFrame):
    """Dark, minimal spectrogram with no histogram side panel."""

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        self.title = QLabel("Spectrogram")
        self.title.setObjectName("panelTitle")
        layout.addWidget(self.title)

        body = QWidget()
        self._stack = QStackedLayout(body)

        self.empty = QLabel("No spectrogram loaded yet.")
        self.empty.setObjectName("emptyState")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setWordWrap(True)
        self._stack.addWidget(self.empty)

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
        self.plot.setMouseEnabled(x=False, y=False)

        self.image = pg.ImageItem()
        self.image.setOpts(axisOrder="row-major")
        self.plot.addItem(self.image)
        self.plot.setAspectLocked(False)
        self._stack.addWidget(self.plot)
        layout.addWidget(body, 1)

        self._reveal = QVariantAnimation(self)
        self._reveal.setStartValue(0.0)
        self._reveal.setEndValue(1.0)
        self._reveal.setDuration(600)
        self._reveal.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._reveal.valueChanged.connect(lambda v: self.image.setOpacity(float(v)))

    def clear(self):
        self._reveal.stop()
        self.image.clear()
        self.title.setText("Spectrogram")
        self._stack.setCurrentWidget(self.empty)

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
        self.title.setText("Spectrogram  ·  model input, mean of 4 regions")
        self._stack.setCurrentWidget(self.plot)
        self.image.setOpacity(0.0)
        self._reveal.start()

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
