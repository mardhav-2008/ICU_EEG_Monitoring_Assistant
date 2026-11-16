from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class EEGPlot(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)

        self.title = QLabel("EEG SIGNAL  /  WAITING FOR RECORDING")
        self.title.setObjectName("fieldLabel")
        layout.addWidget(self.title)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#0a1c24")
        self.plot.showGrid(x=True, y=True, alpha=0.18)
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.setLabel("left", "Channel (offset display)")
        self.plot.setMouseEnabled(x=True, y=False)
        self.plot.getPlotItem().hideButtons()
        layout.addWidget(self.plot)

        self._curves = []

    def clear(self):
        self.plot.clear()
        self._curves.clear()
        self.title.setText("EEG SIGNAL  /  WAITING FOR RECORDING")

    def set_signal(self, signal, channels, sampling_rate, offset_seconds=0.0):
        signal = np.asarray(signal, dtype=np.float32)
        if signal.ndim != 2 or signal.shape[0] == 0:
            self.clear()
            return

        self.plot.clear()
        self._curves.clear()

        channel_count, sample_count = signal.shape
        times = (
            np.arange(sample_count, dtype=np.float32) / float(sampling_rate)
            + float(offset_seconds)
        )

        # Robust per-channel scaling is solely for visual readability.
        for index in range(channel_count):
            values = np.nan_to_num(signal[index], nan=0.0, posinf=0.0, neginf=0.0)
            spread = float(np.percentile(np.abs(values), 95)) if values.size else 1.0
            scale = max(spread, 1e-6)
            display = (values / scale) * 0.8 + index * 2.5
            name = str(channels[index]) if index < len(channels) else f"CH {index + 1:02d}"
            curve = self.plot.plot(
                times,
                display,
                pen=pg.mkPen("#4ee7d0", width=1),
                name=name,
            )
            self._curves.append(curve)

        self.title.setText(
            f"EEG SIGNAL  /  {channel_count} CHANNELS  ·  "
            f"{sample_count / float(sampling_rate):.1f} SEC"
        )
        self.plot.setLabel("bottom", "Recording time", units="s")
        self.plot.enableAutoRange()
