from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class EEGPlot(QFrame):
    """Multichannel EEG viewer styled as a dark glass instrument panel."""

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 12)
        layout.setSpacing(8)

        self.title = QLabel("EEG SIGNAL  /  WAITING FOR RECORDING")
        self.title.setObjectName("fieldLabel")
        layout.addWidget(self.title)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#101D20")
        self.plot.showGrid(x=True, y=True, alpha=0.16)
        self.plot.setLabel("bottom", "Recording time", units="s", color="#9AAFA3")
        self.plot.setLabel("left", "Channel", color="#9AAFA3")
        for axis_name in ("bottom", "left"):
            axis = self.plot.getAxis(axis_name)
            axis.setTextPen("#9AAFA3")
            axis.setPen("#53665C")
        self.plot.setMouseEnabled(x=True, y=False)
        self.plot.getPlotItem().hideButtons()
        self.plot.getPlotItem().setMenuEnabled(False)
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
        times = np.arange(sample_count, dtype=np.float32) / float(sampling_rate)
        times += float(offset_seconds)

        ticks = []
        palette = ["#A8D4B2", "#D2B77B", "#C18C75", "#8CB9A5"]
        for index in range(channel_count):
            values = np.nan_to_num(signal[index], nan=0.0, posinf=0.0, neginf=0.0)
            scale = max(float(np.percentile(np.abs(values), 95)), 1e-6)
            display = (values / scale) * 0.38 + (channel_count - index - 1) * 1.15
            name = str(channels[index]) if index < len(channels) else f"CH {index + 1:02d}"
            curve = self.plot.plot(
                times, display,
                pen=pg.mkPen(palette[index % len(palette)], width=1.1)
            )
            self._curves.append(curve)
            ticks.append(((channel_count - index - 1) * 1.15, name))

        self.plot.getAxis("left").setTicks([ticks])
        self.plot.setYRange(-0.7, max(channel_count * 1.15, 1), padding=0.02)
        self.plot.setXRange(float(times[0]), float(times[-1]), padding=0.01)
        self.title.setText(
            f"EEG SIGNAL  /  {channel_count} CHANNELS  ·  "
            f"{sample_count / float(sampling_rate):.1f} SEC"
        )
