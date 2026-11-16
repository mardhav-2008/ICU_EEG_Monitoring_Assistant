from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QDoubleSpinBox, QFormLayout, QFrame,
)

from gui.services.inference_service import InferenceService
from gui.workers.inference_worker import InferenceWorker
from gui.widgets.eeg_plot import EEGPlot
from gui.widgets.spectrogram import SpectrogramWidget
from gui.widgets.prediction_panel import PredictionPanel


class EEGDashboardPage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.service = InferenceService()
        self._thread = None
        self._worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        header = QHBoxLayout()
        back = QPushButton("← Body map")
        back.clicked.connect(self.back_requested.emit)
        header.addWidget(back)

        title = QLabel("BRAIN  /  EEG MONITORING")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()

        research = QLabel("RESEARCH MODE · NOT FOR CLINICAL DECISIONS")
        research.setObjectName("footnote")
        header.addWidget(research)
        layout.addLayout(header)

        input_panel = QFrame()
        input_panel.setObjectName("panel")
        input_layout = QVBoxLayout(input_panel)

        input_title = QLabel("RECORDING INPUT")
        input_title.setObjectName("fieldLabel")
        input_layout.addWidget(input_title)

        form = QFormLayout()
        self.eeg_path = QLineEdit()
        self.eeg_path.setReadOnly(True)
        self.eeg_path.setPlaceholderText("Choose EEG .parquet file")
        eeg_row = QHBoxLayout()
        eeg_row.addWidget(self.eeg_path, 1)
        eeg_browse = QPushButton("Browse…")
        eeg_browse.clicked.connect(self._browse_eeg)
        eeg_row.addWidget(eeg_browse)
        form.addRow("EEG recording", eeg_row)

        self.spec_path = QLineEdit()
        self.spec_path.setReadOnly(True)
        self.spec_path.setPlaceholderText("Choose spectrogram .parquet file")
        spec_row = QHBoxLayout()
        spec_row.addWidget(self.spec_path, 1)
        spec_browse = QPushButton("Browse…")
        spec_browse.clicked.connect(self._browse_spectrogram)
        spec_row.addWidget(spec_browse)
        form.addRow("Spectrogram", spec_row)

        offsets = QHBoxLayout()
        self.eeg_offset = QDoubleSpinBox()
        self.eeg_offset.setRange(0, 1_000_000)
        self.eeg_offset.setDecimals(1)
        self.eeg_offset.setSuffix(" s")
        self.eeg_offset.setValue(0.0)

        self.spec_offset = QDoubleSpinBox()
        self.spec_offset.setRange(0, 1_000_000)
        self.spec_offset.setDecimals(1)
        self.spec_offset.setSuffix(" s")
        self.spec_offset.setValue(0.0)

        offsets.addWidget(QLabel("EEG offset"))
        offsets.addWidget(self.eeg_offset)
        offsets.addSpacing(16)
        offsets.addWidget(QLabel("Spectrogram offset"))
        offsets.addWidget(self.spec_offset)
        offsets.addStretch()

        form.addRow("Window offsets", offsets)
        input_layout.addLayout(form)

        actions = QHBoxLayout()
        self.run_button = QPushButton("Run inference  →")
        self.run_button.setObjectName("primary")
        self.run_button.clicked.connect(self._run_inference)
        actions.addWidget(self.run_button)

        self.status = QLabel("MODEL NOT LOADED")
        self.status.setObjectName("statusText")
        actions.addWidget(self.status)
        actions.addStretch()
        input_layout.addLayout(actions)

        layout.addWidget(input_panel)

        cards = QHBoxLayout()
        self.prediction = PredictionPanel()
        cards.addWidget(self.prediction, 3)

        self.spectrogram = SpectrogramWidget()
        cards.addWidget(self.spectrogram, 2)
        layout.addLayout(cards, 2)

        self.eeg = EEGPlot()
        layout.addWidget(self.eeg, 3)

        note = QLabel(
            "Inputs are processed by the repository's existing multimodal "
            "fusion model. Predictions are research outputs, not diagnoses."
        )
        note.setObjectName("footnote")
        layout.addWidget(note)

    def _browse_eeg(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select EEG recording",
            str(Path.cwd() / "data" / "raw" / "train_eegs"),
            "Parquet files (*.parquet);;All files (*)",
        )
        if path:
            self.eeg_path.setText(path)

    def _browse_spectrogram(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select spectrogram recording",
            str(Path.cwd() / "data" / "raw" / "train_spectrograms"),
            "Parquet files (*.parquet);;All files (*)",
        )
        if path:
            self.spec_path.setText(path)

    def _run_inference(self):
        eeg_path = self.eeg_path.text().strip()
        spec_path = self.spec_path.text().strip()

        if not eeg_path or not spec_path:
            self.prediction.set_error(
                "Choose both an EEG Parquet file and its corresponding "
                "spectrogram Parquet file."
            )
            return

        if self._thread is not None and self._thread.isRunning():
            return

        self.run_button.setEnabled(False)
        self.prediction.set_status("RUNNING INFERENCE…")
        self.status.setText("● MODEL RUNNING")
        self.eeg.clear()
        self.spectrogram.clear()

        self._thread = QThread(self)
        self._worker = InferenceWorker(
            self.service,
            eeg_path,
            spec_path,
            self.eeg_offset.value(),
            self.spec_offset.value(),
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_inference_finished)
        self._worker.failed.connect(self._on_inference_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self._thread.start()

    def _on_inference_finished(self, result):
        self.prediction.set_prediction(result)
        self.eeg.set_signal(
            result["eeg_signal"],
            result["eeg_channels"],
            result["eeg_sampling_rate"],
            result["eeg_offset_seconds"],
        )
        self.spectrogram.set_spectrogram(result["spectrogram"])
        self.status.setText(
            f"● INFERENCE COMPLETE · {result['device'].upper()}"
        )

    def _on_inference_failed(self, message):
        self.prediction.set_error(message)
        self.status.setText("● INFERENCE ERROR")

    def _on_thread_finished(self):
        self.run_button.setEnabled(True)
        self._thread = None
        self._worker = None

    def closeEvent(self, event):
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)
        super().closeEvent(event)
