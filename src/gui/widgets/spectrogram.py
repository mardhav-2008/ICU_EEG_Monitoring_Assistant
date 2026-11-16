import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class SpectrogramWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("panel")
        layout = QVBoxLayout(self)
        title = QLabel("SPECTROGRAM  /  PLACEHOLDER")
        title.setObjectName("fieldLabel")
        layout.addWidget(title)
        self.image = pg.ImageView()
        self.image.ui.roiBtn.hide()
        self.image.ui.menuBtn.hide()
        data = np.random.default_rng(7).normal(size=(100, 120))
        self.image.setImage(data, autoLevels=True)
        layout.addWidget(self.image)
