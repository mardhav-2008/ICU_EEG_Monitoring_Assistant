from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QEasingCurve, QVariantAnimation, Qt
from PySide6.QtWidgets import QFrame, QLabel, QStackedLayout, QVBoxLayout, QWidget


class EEGPlot(QFrame):
    """Multichannel EEG viewer styled as a dark glass instrument panel.

    New recordings are drawn left to right, like a chart recorder writing
    the analysed window.
    """

    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        self.setMinimumHeight(240)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(10)

        self.title = QLabel("EEG signal")
        self.title.setObjectName("panelTitle")
        layout.addWidget(self.title)

        body = QWidget()
        self._stack = QStackedLayout(body)

        self.empty = QLabel(
            "No recording loaded. The analysed 10-second window appears here "
            "after inference."
        )
        self.empty.setObjectName("emptyState")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty.setWordWrap(True)
        self._stack.addWidget(self.empty)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#101D20")
        self.plot.showGrid(x=True, y=False, alpha=0.16)
        self.plot.setLabel("bottom", "Recording time", units="s", color="#9AAFA3")
        for axis_name in ("bottom", "left"):
            axis = self.plot.getAxis(axis_name)
            axis.setTextPen("#9AAFA3")
            axis.setPen("#53665C")
        self.plot.getAxis("left").setWidth(44)
        tick_font = self.plot.font()
        tick_font.setPointSize(8)
        self.plot.getAxis("left").setTickFont(tick_font)
        self.plot.setMouseEnabled(x=True, y=False)
        self.plot.getPlotItem().hideButtons()
        self.plot.getPlotItem().setMenuEnabled(False)
        self._stack.addWidget(self.plot)
        layout.addWidget(body, 1)

        self._curves = []
        self._series = []
        self._sweep = QVariantAnimation(self)
        self._sweep.setStartValue(0.0)
        self._sweep.setEndValue(1.0)
        self._sweep.setDuration(1100)
        self._sweep.setEasingCurve(QEasingCurve.Type.OutQuad)
        self._sweep.valueChanged.connect(self._draw_until)

    def clear(self):
        self._sweep.stop()
        self.plot.clear()
        self._curves.clear()
        self._series.clear()
        self.title.setText("EEG signal")
        self._stack.setCurrentWidget(self.empty)

    def set_signal(self, signal, channels, sampling_rate, offset_seconds=0.0):
        signal = np.asarray(signal, dtype=np.float32)
        if signal.ndim != 2 or signal.shape[0] == 0:
            self.clear()
            return

        self._sweep.stop()
        self.plot.clear()
        self._curves.clear()
        self._series.clear()
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
                pen=pg.mkPen(palette[index % len(palette)], width=1.1)
            )
            self._curves.append(curve)
            self._series.append((times, display))
            ticks.append(((channel_count - index - 1) * 1.15, name))

        self.plot.getAxis("left").setTicks([ticks])
        self.plot.setYRange(-0.7, max(channel_count * 1.15, 1), padding=0.02)
        self.plot.setXRange(float(times[0]), float(times[-1]), padding=0.01)
        self.title.setText(
            f"EEG signal  ·  {channel_count} channels  ·  "
            f"{sample_count / float(sampling_rate):.1f} s"
        )
        self._stack.setCurrentWidget(self.plot)
        self._sweep.start()

    def _draw_until(self, fraction):
        for curve, (times, display) in zip(self._curves, self._series):
            end = max(2, int(len(times) * float(fraction)))
            curve.setData(times[:end], display[:end])
