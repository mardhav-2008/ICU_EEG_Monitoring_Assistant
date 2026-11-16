import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class EEGPlot(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        title = QLabel("LIVE EEG SIGNAL  /  20 CHANNELS")
        title.setObjectName("fieldLabel")
        layout.addWidget(title)
        self.plot = pg.PlotWidget()
        self.plot.setBackground("#0a1c24")
        self.plot.showGrid(x=True, y=True, alpha=0.18)
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.setLabel("left", "Amplitude", units="µV")
        self.plot.setMouseEnabled(x=True, y=False)
        self.plot.addLegend()
        layout.addWidget(self.plot)
        self._draw_placeholder()

    def _draw_placeholder(self):
        x = np.linspace(0, 10, 2000)
        for i in range(5):
            y = 8 * np.sin(2 * np.pi * (7 + i) * x) + i * 35
            self.plot.plot(x, y, pen=pg.mkPen("#4ee7d0", width=1), name=f"CH {i+1:02d}")
