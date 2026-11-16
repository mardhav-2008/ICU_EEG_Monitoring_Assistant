from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot


class InferenceWorker(QObject):
    finished = Signal(object)
    failed = Signal(str)

    def __init__(
        self,
        service,
        eeg_path: str,
        spectrogram_path: str,
        eeg_offset_seconds: float,
        spectrogram_offset_seconds: float,
    ):
        super().__init__()
        self.service = service
        self.eeg_path = eeg_path
        self.spectrogram_path = spectrogram_path
        self.eeg_offset_seconds = eeg_offset_seconds
        self.spectrogram_offset_seconds = spectrogram_offset_seconds

    @Slot()
    def run(self):
        try:
            result = self.service.predict_recording(
                self.eeg_path,
                self.spectrogram_path,
                self.eeg_offset_seconds,
                self.spectrogram_offset_seconds,
            )
            self.finished.emit(result)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")
