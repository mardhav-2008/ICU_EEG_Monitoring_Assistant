from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QDoubleSpinBox, QGridLayout, QFrame,
    QProgressBar,
)

from gui.services.inference_service import InferenceService
from gui.workers.inference_worker import InferenceWorker
from gui.widgets.eeg_plot import EEGPlot
from gui.widgets.spectrogram import SpectrogramWidget
from gui.widgets.prediction_panel import PredictionPanel
from gui.widgets.motion import PulseDot


class EEGDashboardPage(QWidget):
    back_requested = Signal()

    def __init__(self):
        super().__init__()
        self.service = InferenceService()
        self._thread = None
        self._worker = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(14)
        back = QPushButton("←  Body map")
        back.setObjectName("ghost")
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.clicked.connect(self.back_requested.emit)
        header.addWidget(back)

        title = QLabel("Brain  ·  EEG monitoring")
        title.setObjectName("sectionTitle")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        input_panel = QFrame()
        input_panel.setObjectName("panel")
        input_layout = QVBoxLayout(input_panel)
        input_layout.setContentsMargins(22, 18, 22, 16)
        input_layout.setSpacing(12)

        input_title = QLabel("Recording input")
        input_title.setObjectName("panelTitle")
        input_layout.addWidget(input_title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(12)

        self.eeg_path = QLineEdit()
        self.eeg_path.setReadOnly(True)
        self.eeg_path.setPlaceholderText("Choose EEG .parquet file")
        eeg_browse = QPushButton("Browse…")
        eeg_browse.clicked.connect(self._browse_eeg)

        self.spec_path = QLineEdit()
        self.spec_path.setReadOnly(True)
        self.spec_path.setPlaceholderText("Choose spectrogram .parquet file")
        spec_browse = QPushButton("Browse…")
        spec_browse.clicked.connect(self._browse_spectrogram)

        self.eeg_offset = self._offset_box()
        self.spec_offset = self._offset_box()

        grid.addWidget(self._row_label("EEG recording"), 0, 0)
        grid.addWidget(self.eeg_path, 0, 1)
        grid.addWidget(eeg_browse, 0, 2)
        grid.addWidget(self._row_label("EEG offset"), 0, 3)
        grid.addWidget(self.eeg_offset, 0, 4)

        grid.addWidget(self._row_label("Spectrogram"), 1, 0)
        grid.addWidget(self.spec_path, 1, 1)
        grid.addWidget(spec_browse, 1, 2)
        grid.addWidget(self._row_label("Spectrogram offset"), 1, 3)
        grid.addWidget(self.spec_offset, 1, 4)
        grid.setColumnStretch(1, 1)
        grid.setColumnMinimumWidth(3, 130)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.status_dot = PulseDot("#8FA29A")
        self.status = QLabel("Model not loaded")
        self.status.setObjectName("statusText")
        actions.addWidget(self.status_dot)
        actions.addWidget(self.status)
        actions.addStretch()
        self.run_button = QPushButton("Run inference  →")
        self.run_button.setObjectName("primary")
        self.run_button.setMinimumWidth(180)
        self.run_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.run_button.clicked.connect(self._run_inference)
        actions.addWidget(self.run_button)

        input_layout.addLayout(grid)
        input_layout.addLayout(actions)

        self.busy = QProgressBar()
        self.busy.setObjectName("busy")
        self.busy.setRange(0, 0)
        self.busy.setTextVisible(False)
        self.busy.setVisible(False)
        input_layout.addWidget(self.busy)

        layout.addWidget(input_panel)

        # Signals on the left (spectrogram over EEG), the model's reading
        # in a fixed-width column on the right.
        content = QHBoxLayout()
        content.setSpacing(12)
        signals = QVBoxLayout()
        signals.setSpacing(12)
        self.spectrogram = SpectrogramWidget()
        signals.addWidget(self.spectrogram, 2)
        self.eeg = EEGPlot()
        signals.addWidget(self.eeg, 3)
        content.addLayout(signals, 1)

        self.prediction = PredictionPanel()
        self.prediction.setFixedWidth(420)
        content.addWidget(self.prediction)
        layout.addLayout(content, 1)

        note = QLabel(
            "Inputs are processed by the repository's existing multimodal "
            "fusion model. Predictions are research outputs, not diagnoses."
        )
        note.setObjectName("footnote")
        layout.addWidget(note)

    @staticmethod
    def _row_label(text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        return label

    @staticmethod
    def _offset_box():
        box = QDoubleSpinBox()
        box.setRange(0, 1_000_000)
        box.setDecimals(1)
        box.setSuffix(" s")
        box.setValue(0.0)
        box.setFixedWidth(110)
        box.lineEdit().setTextMargins(10, 0, 0, 0)
        return box

    def _set_running(self, running, text, color):
        self.status.setText(text)
        self.status_dot.set_state(color, active=running)
        self.busy.setVisible(running)

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
        self.prediction.set_status("Running inference…")
        self._set_running(True, "Model running", "#D2B77B")
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
        self._set_running(
            False, f"Inference complete  ·  {result['device']}", "#A7C9A8"
        )

    def _on_inference_failed(self, message):
        self.prediction.set_error(message)
        self._set_running(False, "Inference error", "#F0A18E")

    def _on_thread_finished(self):
        self.run_button.setEnabled(True)
        self._thread = None
        self._worker = None

    def closeEvent(self, event):
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)
        super().closeEvent(event)
