from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
from gui.widgets.eeg_plot import EEGPlot
from gui.widgets.spectrogram import SpectrogramWidget
from gui.widgets.prediction_panel import PredictionPanel


class EEGDashboardPage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        header = QHBoxLayout()
        back = QPushButton("← Body map")
        back.clicked.connect(self.back_requested.emit)
        header.addWidget(back)
        title = QLabel("BRAIN  /  EEG MONITORING")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel("RESEARCH MODE"))
        layout.addLayout(header)

        cards = QHBoxLayout()
        self.prediction = PredictionPanel()
        cards.addWidget(self.prediction, 1)
        self.spectrogram = SpectrogramWidget()
        cards.addWidget(self.spectrogram, 1)
        layout.addLayout(cards)
        self.eeg = EEGPlot()
        layout.addWidget(self.eeg, 2)
        note = QLabel("Inference integration point: connect the existing project pipeline in services/inference_service.py.")
        note.setObjectName("footnote")
        layout.addWidget(note)
